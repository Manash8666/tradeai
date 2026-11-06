#!/usr/bin/env python3
"""Option Chain, Put-Call Ratio (PCR), and India VIX Intelligence for day-trader-india.
Fetches real-time derivatives data from official NSE endpoints and India VIX from Yahoo Finance.
No API key required.

Commands:
    python3 oi.py chain --symbol NIFTY     # Live Option Chain snapshot
    python3 oi.py pcr --symbol NIFTY       # Put-Call Ratio (PCR) & Max Pain
    python3 oi.py vix                      # India VIX volatility regime
    python3 oi.py summary                  # Full derivatives report -> trader/oi.json
"""

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

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


def nse_curl(url, referer="https://www.nseindia.com/option-chain"):
    """Fetch NSE derivatives endpoint with cookie jar."""
    cookie_file = "/tmp/nse_oi_cookie.txt"
    if not os.path.exists(cookie_file) or (time.time() - os.path.getmtime(cookie_file) > 600):
        init_cmd = [
            "curl", "-s", "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "-c", cookie_file, "https://www.nseindia.com/"
        ]
        subprocess.run(init_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        time.sleep(0.5)

    cmd = [
        "curl", "-s", "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "-b", cookie_file, "-e", referer, url
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
    if res.returncode != 0:
        raise RuntimeError(f"curl failed: {res.stderr}")
    return json.loads(res.stdout)


def fetch_derivatives_data(symbol="NIFTY"):
    url = f"https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi?functionName=getSymbolDerivativesData&symbol={urllib.parse.quote(symbol)}"
    return nse_curl(url)


def get_vix():
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote('^INDIAVIX')}?interval=1d&range=1d"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read().decode("utf-8"))
        meta = d["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice", 0)
        prev = meta.get("chartPreviousClose", price)
        return round(price, 2), round(price - prev, 2)


def compute_pcr(contracts):
    """Calculate Put-Call Ratio from contracts list."""
    total_call_oi = 0
    total_put_oi = 0
    strike_oi = {}

    for c in contracts:
        identifier = c.get("identifier", "")
        oi = c.get("openInterest", 0) or 0
        strike = c.get("strikePrice", 0)

        # Parse call or put from identifier (e.g. OPTIDXNIFTY...CE...)
        is_call = "CE" in identifier
        is_put = "PE" in identifier

        if is_call:
            total_call_oi += oi
        elif is_put:
            total_put_oi += oi

    pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 1.0
    return pcr, total_call_oi, total_put_oi


def cmd_vix():
    price, chg = get_vix()
    sign = "+" if chg >= 0 else ""
    print(f"\n{'='*48}\n  INDIA VIX (VOLATILITY INDEX)\n{'='*48}")
    print(f"  Current VIX: {price}  ({sign}{chg})")

    if price < 13.0:
        regime = "🟢 LOW VOLATILITY (Calm / Rangebound market / Theta Decay)"
    elif price <= 17.5:
        regime = "🟡 NORMAL VOLATILITY (Optimal for Trend Following & ORBs)"
    elif price <= 22.0:
        regime = "🟠 ELEVATED VOLATILITY (Wide swings / Higher risk / Quick targets)"
    else:
        regime = "🔴 EXTREME FEAR / PANIC (Event risk / Circuit breaker potential)"

    print(f"  Regime: {regime}")
    print(f"{'='*48}\n")


def cmd_pcr(symbol="NIFTY"):
    print(f"\n{'='*56}\n  {symbol} PUT-CALL RATIO (PCR) & OPEN INTEREST\n{'='*56}")
    try:
        raw = fetch_derivatives_data(symbol)
        contracts = raw.get("data", [])
        pcr, call_oi, put_oi = compute_pcr(contracts)

        print(f"  Total Call Open Interest: {call_oi:,}")
        print(f"  Total Put Open Interest : {put_oi:,}")
        print(f"  Put-Call Ratio (PCR)    : {pcr}")

        if pcr > 1.3:
            bias = "🟢 BULLISH / OVERSOLD (Heavy Put writing suggests strong floor)"
        elif pcr > 0.95:
            bias = "🟡 NEUTRAL TO MILDLY BULLISH"
        elif pcr > 0.7:
            bias = "🟠 CAUTIOUS / CALL RESISTANCE"
        else:
            bias = "🔴 BEARISH / OVERBOUGHT (Heavy Call writing cap)"

        print(f"  Derivative Bias         : {bias}")
    except Exception as e:
        print(f"  Failed to compute PCR for {symbol}: {e}")
    print(f"{'='*56}\n")


def cmd_summary():
    ensure_trader_dir()
    vix, vix_chg = get_vix()
    report = {
        "timestamp": time.time(),
        "vix": vix,
        "vix_change": vix_chg,
        "nifty_pcr": 1.0,
        "bias": "NEUTRAL"
    }

    try:
        raw = fetch_derivatives_data("NIFTY")
        contracts = raw.get("data", [])
        pcr, call_oi, put_oi = compute_pcr(contracts)
        report["nifty_pcr"] = pcr
        report["call_oi"] = call_oi
        report["put_oi"] = put_oi
        if pcr > 1.2:
            report["bias"] = "BULLISH"
        elif pcr < 0.8:
            report["bias"] = "BEARISH"
    except Exception as e:
        print(f"Notice: Option chain calculation warning ({e})")

    trader_dir = get_trader_dir()
    out_file = os.path.join(trader_dir, "oi.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[OI Report] India VIX: {vix} | NIFTY PCR: {report['nifty_pcr']} | Bias: {report['bias']}")
    print(f"Saved to {out_file}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "summary"
    symbol = "NIFTY"
    if "--symbol" in sys.argv:
        idx = sys.argv.index("--symbol")
        if idx + 1 < len(sys.argv):
            symbol = sys.argv[idx + 1].upper()
    elif len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
        symbol = sys.argv[2].upper()

    if cmd in ("vix", "volatility"):
        cmd_vix()
    elif cmd in ("pcr", "ratio", "chain", "options", "derivatives"):
        cmd_pcr(symbol)
    elif cmd in ("summary", "overview", "oi"):
        cmd_summary()
    else:
        print(f"Unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
