#!/usr/bin/env python3
"""Exit & Auto-Squareoff Planner for day-trader-india.
Plans exact Stop-Loss, Take-Profit targets, and enforces the mandatory
15:15 IST auto-squareoff exit before Indian brokers apply penalty fees.

Commands:
    python3 exit.py plan                           # Plan exit from trader/setup.json -> trader/plan.json
    python3 exit.py calc --entry 1250 --stop 1240  # Calculate targets manually
"""

import json
import os
import sys

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


def calculate_exit(symbol, direction, entry, orb_high, orb_low, orb_mid):
    if direction == "LONG":
        # Stop at range midpoint for tight risk, or range low for wider breathing room
        stop_loss = orb_mid
        risk_per_share = round(entry - stop_loss, 2)
        if risk_per_share <= 0:
            stop_loss = round(entry * 0.995, 2)
            risk_per_share = round(entry - stop_loss, 2)

        target_1 = round(entry + (1.5 * risk_per_share), 2)  # 1:1.5 RR
        target_2 = round(entry + (2.0 * risk_per_share), 2)  # 1:2.0 RR

    else:  # SHORT
        stop_loss = orb_mid
        risk_per_share = round(stop_loss - entry, 2)
        if risk_per_share <= 0:
            stop_loss = round(entry * 1.005, 2)
            risk_per_share = round(stop_loss - entry, 2)

        target_1 = round(entry - (1.5 * risk_per_share), 2)
        target_2 = round(entry - (2.0 * risk_per_share), 2)

    return {
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry,
        "stop_loss": stop_loss,
        "risk_per_share": risk_per_share,
        "target_1_5r": target_1,
        "target_2r": target_2,
        "hard_time_cutoff": "15:15 IST",
        "auto_squareoff_notice": "Position MUST be closed before 15:15 IST to avoid broker MIS auto-squareoff penalty charges (₹50+GST)."
    }


def cmd_plan():
    ensure_trader_dir()
    trader_dir = get_trader_dir()
    setup_path = os.path.join(trader_dir, "setup.json")
    if not os.path.exists(setup_path):
        print("No setup.json found. Run trader-entry first.")
        return

    with open(setup_path, "r", encoding="utf-8") as f:
        setup = json.load(f)

    if setup.get("status") != "TRIGGERED":
        print(f"Setup is not triggered yet (current status: {setup.get('status')})")
        return

    plan = calculate_exit(
        setup["symbol"],
        setup["direction"],
        setup["entry_price"],
        setup["orb_high"],
        setup["orb_low"],
        setup["orb_midpoint"]
    )

    out_file = os.path.join(trader_dir, "plan.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    print(f"\n{'='*56}\n  INTRADAY EXIT PLAN: {plan['symbol']} ({plan['direction']})\n{'='*56}")
    print(f"  Entry Price      : ₹{plan['entry_price']}")
    print(f"  Stop-Loss        : ₹{plan['stop_loss']}  (Risk: ₹{plan['risk_per_share']} / share)")
    print(f"  Target 1 (1:1.5R): ₹{plan['target_1_5r']}  (Profit: ₹{round(1.5 * plan['risk_per_share'], 2)})")
    print(f"  Target 2 (1:2.0R): ₹{plan['target_2r']}  (Profit: ₹{round(2.0 * plan['risk_per_share'], 2)})")
    print(f"  Hard Time Stop   : {plan['hard_time_cutoff']} (MANDATORY SQUARE-OFF)")
    print(f"{'='*56}\n")
    print(f"Saved exit plan to {out_file}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "plan"
    if cmd in ("plan", "calc", "target", "targets", "stop"):
        cmd_plan()
    else:
        print(f"Unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
