#!/usr/bin/env python3
"""Intraday Entry Timer for day-trader-india.
Monitors 5-minute bars for confirmation of 15-min Opening Range Breakouts (ORB)
and VWAP alignment. Free Yahoo 5m data.

Commands:
    python3 entry.py watch --symbol RELIANCE.NS   # Check bar-by-bar entry trigger
    python3 entry.py check                        # Check all candidates in trader/orb_candidates.json
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
UA = "Mozilla/5.0 (compatible; day-trader-india/1.0; +https://github.com/kapish/day-trader-india)"
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


def get_5m_bars(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?interval=5m&range=1d"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read().decode("utf-8"))
    res = d["chart"]["result"][0]
    quotes = res["indicators"]["quote"][0]
    timestamps = res.get("timestamp", [])
    closes = quotes.get("close", [])
    highs = quotes.get("high", [])
    lows = quotes.get("low", [])
    volumes = quotes.get("volume", [])

    bars = []
    for i in range(len(closes)):
        if closes[i] is not None and highs[i] is not None and lows[i] is not None:
            ts = timestamps[i] if i < len(timestamps) else 0
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(IST)
            bars.append({
                "time": dt.strftime("%H:%M"),
                "high": round(highs[i], 2),
                "low": round(lows[i], 2),
                "close": round(closes[i], 2),
                "volume": volumes[i] or 0
            })
    return bars


def compute_vwap(bars):
    cum_vol = 0
    cum_pv = 0.0
    for b in bars:
        typical = (b["high"] + b["low"] + b["close"]) / 3.0
        v = b["volume"]
        cum_vol += v
        cum_pv += typical * v
    return round(cum_pv / cum_vol, 2) if cum_vol > 0 else bars[-1]["close"]


def check_symbol_entry(symbol):
    bars = get_5m_bars(symbol)
    if len(bars) < 3:
        return {"symbol": symbol, "status": "WAITING", "reason": "Fewer than 3 bars (Opening Range still forming)"}

    # 15-min range: first 3 bars (09:15, 09:20, 09:25)
    orb_high = max(b["high"] for b in bars[:3])
    orb_low = min(b["low"] for b in bars[:3])
    orb_mid = round((orb_high + orb_low) / 2.0, 2)
    vwap = compute_vwap(bars)

    avg_vol = sum(b["volume"] for b in bars) / len(bars) if bars else 1

    # Check subsequent bars for a close above ORB high or below ORB low
    for b in bars[3:]:
        if b["close"] > orb_high:
            vwap_confirmed = b["close"] >= vwap
            vol_surge = b["volume"] >= (avg_vol * 1.1)
            return {
                "symbol": symbol,
                "status": "TRIGGERED",
                "direction": "LONG",
                "entry_price": b["close"],
                "trigger_time": b["time"],
                "orb_high": orb_high,
                "orb_low": orb_low,
                "orb_midpoint": orb_mid,
                "vwap": vwap,
                "vwap_confirmed": vwap_confirmed,
                "volume_confirmed": vol_surge
            }
        elif b["close"] < orb_low:
            vwap_confirmed = b["close"] <= vwap
            vol_surge = b["volume"] >= (avg_vol * 1.1)
            return {
                "symbol": symbol,
                "status": "TRIGGERED",
                "direction": "SHORT",
                "entry_price": b["close"],
                "trigger_time": b["time"],
                "orb_high": orb_high,
                "orb_low": orb_low,
                "orb_midpoint": orb_mid,
                "vwap": vwap,
                "vwap_confirmed": vwap_confirmed,
                "volume_confirmed": vol_surge
            }

    curr_price = bars[-1]["close"]
    return {
        "symbol": symbol,
        "status": "WAITING",
        "current_price": curr_price,
        "orb_high": orb_high,
        "orb_low": orb_low,
        "vwap": vwap,
        "reason": f"Inside 15m range (₹{orb_low} - ₹{orb_high})"
    }


def cmd_watch(symbol):
    ensure_trader_dir()
    clean_sym = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
    print(f"\n[Entry Timer] Evaluating {clean_sym}...")
    res = check_symbol_entry(clean_sym)
    print(f"  Status        : {res['status']}")
    if res['status'] == "TRIGGERED":
        print(f"  Direction     : {res['direction']}")
        print(f"  Entry Price   : ₹{res['entry_price']}  (Triggered at {res['trigger_time']} IST)")
        print(f"  15m Range     : High ₹{res['orb_high']} | Low ₹{res['orb_low']}")
        print(f"  VWAP          : ₹{res['vwap']} (Aligned: {res['vwap_confirmed']})")
        print(f"  Volume Surge  : {res['volume_confirmed']}")
        trader_dir = get_trader_dir()
        out_file = os.path.join(trader_dir, "setup.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        print(f"  ✓ Saved triggered setup to {out_file}")
    else:
        print(f"  Current Price : ₹{res.get('current_price', 'N/A')}")
        print(f"  Reason        : {res.get('reason')}")
    print()


def cmd_check():
    ensure_trader_dir()
    trader_dir = get_trader_dir()
    orb_path = os.path.join(trader_dir, "orb_candidates.json")
    if not os.path.exists(orb_path):
        print("No orb_candidates.json found. Run trader-scanner orb first.")
        return
    with open(orb_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"[Entry Timer] Checking {len(candidates)} candidates for entry confirmation...")
    triggered = []
    for c in candidates:
        res = check_symbol_entry(c["symbol"])
        if res["status"] == "TRIGGERED":
            triggered.append(res)
            print(f"  ⚡ TRIGGERED: {res['symbol']} {res['direction']} @ ₹{res['entry_price']}")
        time.sleep(0.1)

    if triggered:
        out_file = os.path.join(trader_dir, "setup.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(triggered[0], f, indent=2)
        print(f"\nSaved primary setup to {out_file}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "check"
    if cmd in ("watch", "eval", "evaluate", "symbol"):
        sym = "RELIANCE.NS"
        if "--symbol" in sys.argv:
            idx = sys.argv.index("--symbol")
            if idx + 1 < len(sys.argv):
                sym = sys.argv[idx + 1]
        elif len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
            sym = sys.argv[2]

        sym = sym.upper()
        if not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
            sym = f"{sym}.NS"
        cmd_watch(sym)
    elif cmd in ("check", "scan", "orb"):
        cmd_check()
    elif not cmd.startswith("-"):
        sym = cmd.upper()
        if not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
            sym = f"{sym}.NS"
        cmd_watch(sym)
    else:
        print(f"Unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
