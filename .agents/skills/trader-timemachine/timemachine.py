#!/usr/bin/env python3
"""Time Machine (Monte Carlo Simulator) for day-trader-india.
Replays the rest of the Indian intraday session 10,000 times using the stock's
own recent 5-minute candle distributions to estimate honest win/loss probabilities
before risking real capital.

Commands:
    python3 timemachine.py replay            # Replay trade from trader/plan.json
    python3 timemachine.py replay --runs 5000
"""

import json
import os
import random
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


def fetch_historical_bars(symbol):
    """Fetch recent 5m intraday bars from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?interval=5m&range=5d"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read().decode("utf-8"))
    res = d["chart"]["result"][0]
    quotes = res["indicators"]["quote"][0]
    closes = quotes.get("close", [])
    highs = quotes.get("high", [])
    lows = quotes.get("low", [])

    deltas = []
    for i in range(1, len(closes)):
        if closes[i] is not None and closes[i - 1] is not None and highs[i] is not None and lows[i] is not None:
            prev = closes[i - 1]
            deltas.append({
                "high_pct": (highs[i] - prev) / prev,
                "low_pct": (lows[i] - prev) / prev,
                "close_pct": (closes[i] - prev) / prev
            })
    return deltas


def run_monte_carlo(plan, deltas, runs=10000, remaining_bars=50):
    entry = plan["entry_price"]
    stop = plan["stop_loss"]
    target = plan["target_1_5r"]
    direction = plan.get("direction", "LONG")

    target_hits = 0
    stop_hits = 0
    expired = 0

    random.seed(42)  # Deterministic seed for reproducible testing

    for _ in range(runs):
        curr_price = entry
        hit = False
        for _ in range(remaining_bars):
            sample = random.choice(deltas)
            bar_high = curr_price * (1.0 + sample["high_pct"])
            bar_low = curr_price * (1.0 + sample["low_pct"])
            curr_price = curr_price * (1.0 + sample["close_pct"])

            if direction == "LONG":
                if bar_low <= stop:
                    stop_hits += 1
                    hit = True
                    break
                if bar_high >= target:
                    target_hits += 1
                    hit = True
                    break
            else:  # SHORT
                if bar_high >= stop:
                    stop_hits += 1
                    hit = True
                    break
                if bar_low <= target:
                    target_hits += 1
                    hit = True
                    break

        if not hit:
            expired += 1

    target_pct = round((target_hits / runs) * 100, 1)
    stop_pct = round((stop_hits / runs) * 100, 1)
    expired_pct = round((expired / runs) * 100, 1)

    # Expected value (EV) per ₹1 of risk
    risk = abs(entry - stop)
    reward = abs(target - entry)
    ev_per_rupee = round(((target_pct / 100.0) * reward - (stop_pct / 100.0) * risk) / risk, 2)

    return {
        "runs": runs,
        "target_hit_pct": target_pct,
        "stop_hit_pct": stop_pct,
        "flat_by_close_pct": expired_pct,
        "reward_risk_ratio": round(reward / risk, 2) if risk else 1.0,
        "expected_value_per_rupee": ev_per_rupee,
        "verdict": "FAVORABLE" if ev_per_rupee > 0.15 else "MARGINAL" if ev_per_rupee >= 0 else "UNFAVORABLE"
    }


def cmd_replay(runs=10000):
    trader_dir = get_trader_dir()
    plan_path = os.path.join(trader_dir, "plan.json")
    if not os.path.exists(plan_path):
        print("No plan.json found. Run trader-exit first.")
        return

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    symbol = plan["symbol"]
    print(f"\n[Time Machine] Replaying {symbol} trade {runs:,} times to 15:15 IST...")
    try:
        deltas = fetch_historical_bars(symbol)
        if len(deltas) < 30:
            print("Not enough historical 5m bars to simulate accurately.")
            return

        result = run_monte_carlo(plan, deltas, runs=runs)
        print(f"\n{'='*56}\n  MONTE CARLO PROBABILITY REPORT ({runs:,} RUNS)\n{'='*56}")
        print(f"  Target Hit (Win)     : {result['target_hit_pct']}%")
        print(f"  Stop Hit   (Loss)    : {result['stop_hit_pct']}%")
        print(f"  Flat by 15:15 IST    : {result['flat_by_close_pct']}%")
        print(f"  Reward / Risk Ratio  : {result['reward_risk_ratio']}:1")
        print(f"  Expected Value (EV)  : ₹{result['expected_value_per_rupee']} per ₹1 risked")
        print(f"  Trade Verdict        : [{result['verdict']}]")
        print(f"{'='*56}\n")

        out_file = os.path.join(trader_dir, "timemachine.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"Saved replay report to {out_file}")

    except Exception as e:
        print(f"Time Machine replay error: {e}")


def main():
    runs = 10000
    if "--runs" in sys.argv:
        idx = sys.argv.index("--runs")
        if idx + 1 < len(sys.argv):
            runs = int(sys.argv[idx + 1])
    cmd_replay(runs)


if __name__ == "__main__":
    main()
