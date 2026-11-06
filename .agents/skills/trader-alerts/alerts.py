#!/usr/bin/env python3
"""Price & Time Alerts for day-trader-india.
Monitors price targets, stop losses, and time-based alerts (09:15 Open, 09:30 ORB completion,
15:10 IST pre-squareoff warning).

Commands:
    python3 alerts.py check                        # Check all active alerts against live prices
    python3 alerts.py add --symbol TCS --price 4100 # Add a custom price alert
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


def get_live_price(symbol):
    clean_sym = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(clean_sym)}?interval=1m&range=1d"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=8) as r:
        d = json.loads(r.read().decode("utf-8"))
    meta = d["chart"]["result"][0]["meta"]
    return meta.get("regularMarketPrice", 0)


def cmd_check():
    trader_dir = get_trader_dir()
    now_ist = datetime.now(timezone.utc).astimezone(IST)
    curr_hm = now_ist.strftime("%H:%M")

    print(f"\n[Alerts Monitor] Current time: {curr_hm} IST")

    # Time milestones
    if curr_hm == "09:15":
        print("  🔔 OPENING BELL (09:15 IST): Market is now open!")
    elif curr_hm == "09:30":
        print("  🔔 15-MIN ORB COMPLETE (09:30 IST): Opening range set. Run trader-entry watch!")
    elif curr_hm >= "15:10":
        print("  ⚠️ TIME WARNING: Past 15:10 IST! Close all MIS positions before 15:15 to avoid auto-squareoff penalties!")

    # Check open positions
    trades_file = os.path.join(trader_dir, "trades.json")
    if os.path.exists(trades_file):
        with open(trades_file, "r", encoding="utf-8") as f:
            trades = json.load(f)

        for t in trades:
            if t.get("status") == "OPEN":
                sym = t["symbol"]
                sl = t["stop_loss"]
                tgt = t["target"]
                try:
                    price = get_live_price(sym)
                    print(f"  Checking {sym}: Current ₹{price} (SL: ₹{sl}, TGT: ₹{tgt})")
                    if t["direction"] == "LONG":
                        if price <= sl:
                            print(f"    🚨 STOP LOSS HIT for {sym} at ₹{price}!")
                        elif price >= tgt:
                            print(f"    🎯 TARGET REACHED for {sym} at ₹{price}!")
                    else:
                        if price >= sl:
                            print(f"    🚨 STOP LOSS HIT for {sym} at ₹{price}!")
                        elif price <= tgt:
                            print(f"    🎯 TARGET REACHED for {sym} at ₹{price}!")
                except Exception as e:
                    print(f"  Failed to fetch price for {sym}: {e}")
    print()


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "check"
    if cmd in ("check", "monitor", "status", "watch", "run"):
        cmd_check()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
