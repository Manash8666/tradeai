#!/usr/bin/env python3
"""NSE Chart Scanner for day-trader-india: scan liquid NSE stocks for intraday setups.
Standard library only. Free public endpoints (Yahoo Finance, NSE Archives).

Commands:
    python3 scan.py universe                  # Download NSE 100 / F&O list -> trader/universe.txt
    python3 scan.py daily                     # Pre-market scan of daily setups -> trader/watchlist.json
    python3 scan.py orb                       # 15-min Opening Range Breakouts (after 09:30 IST)
    python3 scan.py indices                   # Live snapshot of Nifty, Bank Nifty, and India VIX
"""

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
UA = "Mozilla/5.0 (compatible; day-trader-india/1.0; +https://github.com/kapish/day-trader-india)"
YAHOO_HOSTS = ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com")
NSE_NIFTY100_URL = "https://archives.nseindia.com/content/indices/ind_nifty100list.csv"

# Curated fallback of top liquid NSE stocks if network is offline
FALLBACK_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "BHARTIARTL.NS", "SBIN.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "TATAMOTORS.NS", "KOTAKBANK.NS", "AXISBANK.NS", "NTPC.NS",
    "TITAN.NS", "ONGC.NS", "POWERGRID.NS", "ADANIPORTS.NS", "TATASTEEL.NS",
    "COALINDIA.NS", "BAJAJFINSV.NS", "M&M.NS", "JSWSTEEL.NS", "ASIANPAINT.NS"
]

def get_trader_dir():
    if "TRADER_DIR" in os.environ:
        return os.environ["TRADER_DIR"]
    if os.path.exists("trader"):
        return "trader"
    elif os.path.exists("../trader"):
        return "../trader"
    return "trader"


def ensure_trader_dir():
    os.makedirs(get_trader_dir(), exist_ok=True)


def http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def yahoo_get(path, timeout=15):
    for host in YAHOO_HOSTS:
        url = f"{host}{path}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except Exception:
            continue
    raise RuntimeError(f"Failed to fetch {path} from all Yahoo endpoints")


def cmd_universe(args):
    """Download official NSE Nifty 100 list and write to trader/universe.txt."""
    ensure_trader_dir()
    trader_dir = get_trader_dir()
    symbols = []
    try:
        raw_csv = http_get(NSE_NIFTY100_URL)
        reader = csv.DictReader(raw_csv.splitlines())
        for row in reader:
            sym = row.get("Symbol", "").strip()
            if sym and not sym.startswith("#"):
                symbols.append(f"{sym}.NS")
        print(f"[Universe] Successfully downloaded {len(symbols)} stocks from NSE Nifty 100.")
    except Exception as e:
        print(f"[Universe] Notice: Could not reach NSE archives ({e}). Using liquid fallback universe.")
        symbols = FALLBACK_UNIVERSE

    out_path = os.path.join(trader_dir, "universe.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        for s in symbols:
            f.write(f"{s}\n")
    print(f"[Universe] Wrote {len(symbols)} tickers to {out_path}")


def rsi_14(closes):
    """Calculate 14-period Wilder RSI."""
    if len(closes) < 15:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(0.0, diff))
        losses.append(max(0.0, -diff))
    
    avg_gain = sum(gains[:14]) / 14.0
    avg_loss = sum(losses[:14]) / 14.0
    for i in range(14, len(gains)):
        avg_gain = (avg_gain * 13 + gains[i]) / 14.0
        avg_loss = (avg_loss * 13 + losses[i]) / 14.0
    
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    if avg_gain == 0:
        return 0.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def cmd_daily(args):
    """Scan daily setups before the 09:15 IST opening bell."""
    ensure_trader_dir()
    trader_dir = get_trader_dir()
    universe_path = os.path.join(trader_dir, "universe.txt")
    if os.path.exists(universe_path):
        with open(universe_path, "r", encoding="utf-8") as f:
            symbols = [line.strip() for line in f if line.strip()]
    else:
        symbols = FALLBACK_UNIVERSE

    limit = 35
    if "--limit" in args:
        idx = args.index("--limit")
        if idx + 1 < len(args):
            limit = int(args[idx + 1])
    symbols = symbols[:limit]

    print(f"[Daily Scan] Scanning {len(symbols)} NSE stocks for daily setups...")
    watchlist = []

    for sym in symbols:
        try:
            encoded_sym = urllib.parse.quote(sym)
            path = f"/v8/finance/chart/{encoded_sym}?interval=1d&range=3mo"
            data = yahoo_get(path)
            res = data["chart"]["result"][0]
            quotes = res["indicators"]["quote"][0]
            closes = [c for c in quotes.get("close", []) if c is not None]
            highs = [h for h in quotes.get("high", []) if h is not None]
            volumes = [v for v in quotes.get("volume", []) if v is not None]

            if len(closes) < 25:
                continue

            last_close = round(closes[-1], 2)
            prev_close = round(closes[-2], 2)
            last_vol = volumes[-1] if volumes else 0
            sma20 = sum(closes[-20:]) / 20.0
            rsi = round(rsi_14(closes), 1)

            setups = []

            # 1. 20-day high breakout
            prior_20_high = max(highs[-21:-1]) if len(highs) >= 21 else max(closes[-21:-1])
            if last_close > prior_20_high:
                setups.append("breakout_20d")

            # 2. Bull flag (Up > 8% over 10 days before last 5, now consolidating in 4% box)
            if len(closes) >= 16:
                base = closes[-15]
                pole_top = max(closes[-15:-5])
                if (pole_top - base) / base >= 0.08:
                    flag_range = (max(closes[-5:]) - min(closes[-5:])) / closes[-5]
                    if flag_range <= 0.04 and last_close >= closes[-2]:
                        setups.append("bull_flag")

            # 3. 20-SMA Reclaim
            if closes[-2] < sma20 and last_close > sma20:
                setups.append("reclaim_sma20")

            # 4. Oversold bounce
            rsi_prev = rsi_14(closes[:-1])
            if rsi_prev < 32 and last_close > prev_close:
                setups.append("oversold_bounce")

            if setups:
                item = {
                    "symbol": sym,
                    "last_close": last_close,
                    "change_pct": round(((last_close - prev_close) / prev_close) * 100, 2),
                    "volume": last_vol,
                    "sma20": round(sma20, 2),
                    "rsi": rsi,
                    "setups": setups
                }
                watchlist.append(item)
                print(f"  ✓ {sym:15} ₹{last_close:<8} RSI:{rsi:<5} Setups: {', '.join(setups)}")

            time.sleep(0.1)
        except Exception:
            continue

    out_file = os.path.join(trader_dir, "watchlist.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, indent=2)
    print(f"\n[Daily Scan] Found {len(watchlist)} candidates. Saved to {out_file}")


def cmd_orb(args):
    """Scan for 15-minute Opening Range Breakouts (ORB) on 5-minute bars.
    Indian Session ORB: 09:15 - 09:30 range (bars 1, 2, 3).
    Breakout occurs when any subsequent bar closes above range high.
    """
    ensure_trader_dir()
    trader_dir = get_trader_dir()
    wl_file = os.path.join(trader_dir, "watchlist.json")
    symbols = []
    if os.path.exists(wl_file):
        with open(wl_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            symbols = [d["symbol"] for d in data]

    if not symbols:
        symbols = FALLBACK_UNIVERSE[:20]

    print(f"[ORB Scan] Scanning {len(symbols)} candidates for 15-min Opening Range Breakouts...")
    candidates = []

    for sym in symbols:
        try:
            encoded_sym = urllib.parse.quote(sym)
            path = f"/v8/finance/chart/{encoded_sym}?interval=5m&range=1d"
            res = yahoo_get(path)["chart"]["result"][0]
            quotes = res["indicators"]["quote"][0]
            closes = quotes.get("close", [])
            highs = quotes.get("high", [])
            lows = quotes.get("low", [])
            volumes = quotes.get("volume", [])

            # Filter valid bars
            valid_bars = []
            for i in range(len(closes)):
                if closes[i] is not None and highs[i] is not None and lows[i] is not None:
                    valid_bars.append({
                        "high": highs[i],
                        "low": lows[i],
                        "close": closes[i],
                        "volume": volumes[i] or 0
                    })

            # Need at least 4 bars (3 bars for 15-min ORB + at least 1 post-ORB bar)
            if len(valid_bars) < 4:
                continue

            # First 3 bars: 09:15-09:20, 09:20-09:25, 09:25-09:30
            orb_high = max(b["high"] for b in valid_bars[:3])
            orb_low = min(b["low"] for b in valid_bars[:3])
            orb_range = round(orb_high - orb_low, 2)
            orb_mid = round((orb_high + orb_low) / 2.0, 2)

            for idx, bar in enumerate(valid_bars[3:], start=4):
                if bar["close"] > orb_high:
                    candidates.append({
                        "symbol": sym,
                        "type": "ORB_BULLISH",
                        "orb_high": round(orb_high, 2),
                        "orb_low": round(orb_low, 2),
                        "orb_range": orb_range,
                        "orb_midpoint": orb_mid,
                        "trigger_close": round(bar["close"], 2),
                        "trigger_bar_index": idx,
                        "extension_pct": round(((bar["close"] - orb_high) / orb_high) * 100, 2)
                    })
                    print(f"  🚀 BULLISH ORB: {sym:14} Breakout at ₹{bar['close']} (Range: ₹{orb_low} - ₹{orb_high})")
                    break
                elif bar["close"] < orb_low:
                    candidates.append({
                        "symbol": sym,
                        "type": "ORB_BEARISH",
                        "orb_high": round(orb_high, 2),
                        "orb_low": round(orb_low, 2),
                        "orb_range": orb_range,
                        "orb_midpoint": orb_mid,
                        "trigger_close": round(bar["close"], 2),
                        "trigger_bar_index": idx,
                        "extension_pct": round(((orb_low - bar["close"]) / orb_low) * 100, 2)
                    })
                    print(f"  🔻 BEARISH ORB: {sym:14} Breakdown at ₹{bar['close']} (Range: ₹{orb_low} - ₹{orb_high})")
                    break

            time.sleep(0.1)
        except Exception:
            continue

    out_file = os.path.join(trader_dir, "orb_candidates.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)
    print(f"\n[ORB Scan] {len(candidates)} breakouts detected. Saved to {out_file}")


def cmd_indices(args):
    """Show live market benchmark dashboard."""
    indices = {
        "NIFTY 50": "^NSEI",
        "BANK NIFTY": "^NSEBANK",
        "NIFTY IT": "^CNXIT",
        "INDIA VIX": "^INDIAVIX",
        "SENSEX": "^BSESN"
    }
    print(f"\n{'='*48}\n  INDIAN MARKET BENCHMARKS (NSE / BSE)\n{'='*48}")
    for name, sym in indices.items():
        try:
            encoded_sym = urllib.parse.quote(sym)
            path = f"/v8/finance/chart/{encoded_sym}?interval=1d&range=1d"
            res = yahoo_get(path)["chart"]["result"][0]
            meta = res["meta"]
            price = meta.get("regularMarketPrice", 0)
            prev = meta.get("chartPreviousClose", price)
            change = price - prev
            chg_pct = (change / prev) * 100 if prev else 0
            sign = "+" if change >= 0 else ""
            print(f"  {name:12}: {price:>10.2f}  ({sign}{change:.2f}, {sign}{chg_pct:.2f}%)")
        except Exception as e:
            print(f"  {name:12}: N/A ({e})")
    print(f"{'='*48}\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "indices"
    args = sys.argv[2:]

    if cmd == "universe":
        cmd_universe(args)
    elif cmd == "daily":
        cmd_daily(args)
    elif cmd == "orb":
        cmd_orb(args)
    elif cmd in ("indices", "dashboard", "overview", "market", "benchmarks"):
        cmd_indices(args)
    else:
        print(f"Unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
