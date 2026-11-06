#!/usr/bin/env python3
"""Position Sizer & Budget Manager for day-trader-india.
Sizes positions in Indian Rupees (₹) according to strict rupee risk per trade
and calculates margin requirements under SEBI's 5x MIS intraday leverage.

Commands:
    python3 size.py size --risk 1000 --capital 50000    # Size position from trader/plan.json
    python3 size.py size                                # Uses defaults (₹1,000 risk, ₹50,000 capital)
"""

import json
import os
import sys

MIS_LEVERAGE = 5.0  # SEBI Peak Intraday Margin allows max 5x for equity cash


def get_trader_dir():
    if "TRADER_DIR" in os.environ:
        return os.environ["TRADER_DIR"]
    if os.path.exists("trader"):
        return "trader"
    elif os.path.exists("../trader"):
        return "../trader"
    return "trader"


def calculate_position_size(symbol, direction, entry, stop, target, risk_per_share, max_risk_inr=1000.0, total_capital_inr=50000.0):
    if risk_per_share <= 0:
        raise ValueError("Invalid risk per share")

    qty = int(max_risk_inr // risk_per_share)
    if qty < 1:
        qty = 1

    total_trade_val = round(qty * entry, 2)
    margin_required = round(total_trade_val / MIS_LEVERAGE, 2)
    actual_risk = round(qty * risk_per_share, 2)
    potential_profit = round(qty * (target - entry if direction == "LONG" else entry - target), 2)

    return {
        "symbol": symbol,
        "direction": direction,
        "product_type": "MIS (Intraday)",
        "quantity": qty,
        "entry_price": entry,
        "stop_loss": stop,
        "target": target,
        "total_value_inr": total_trade_val,
        "margin_required_inr": margin_required,
        "max_risk_inr": actual_risk,
        "potential_profit_inr": potential_profit,
        "capital_inr": total_capital_inr,
        "margin_utilization_pct": round((margin_required / total_capital_inr) * 100, 2) if total_capital_inr > 0 else 0.0
    }


def cmd_size(max_risk_inr=1000.0, total_capital_inr=50000.0):
    trader_dir = get_trader_dir()
    plan_path = os.path.join(trader_dir, "plan.json")
    if not os.path.exists(plan_path):
        print("No plan.json found. Run trader-exit first.")
        return

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    entry = plan["entry_price"]
    stop = plan["stop_loss"]
    target = plan["target_1_5r"]
    risk_per_share = plan["risk_per_share"]
    symbol = plan["symbol"]
    direction = plan.get("direction", "LONG")

    order = calculate_position_size(
        symbol=symbol,
        direction=direction,
        entry=entry,
        stop=stop,
        target=target,
        risk_per_share=risk_per_share,
        max_risk_inr=max_risk_inr,
        total_capital_inr=total_capital_inr
    )

    print(f"\n{'='*56}\n  POSITION SIZING REPORT (SEBI 5x MIS LEVERAGE)\n{'='*56}")
    print(f"  Symbol             : {symbol} ({direction})")
    print(f"  Quantity to Trade  : {order['quantity']} shares")
    print(f"  Total Trade Value  : ₹{order['total_value_inr']:,}")
    print(f"  Margin Required    : ₹{order['margin_required_inr']:,}  ({order['margin_utilization_pct']}% of capital)")
    print(f"  Max Rupee Risk     : ₹{order['max_risk_inr']:,}")
    print(f"  Target Profit      : ₹{order['potential_profit_inr']:,}")
    print(f"{'='*56}\n")

    out_file = os.path.join(trader_dir, "order.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(order, f, indent=2)
    print(f"Saved sized order ticket to {out_file}")


def main():
    risk = 1000.0
    capital = 50000.0

    if "--risk" in sys.argv:
        idx = sys.argv.index("--risk")
        if idx + 1 < len(sys.argv):
            risk = float(sys.argv[idx + 1])

    if "--capital" in sys.argv:
        idx = sys.argv.index("--capital")
        if idx + 1 < len(sys.argv):
            capital = float(sys.argv[idx + 1])

    cmd_size(risk, capital)


if __name__ == "__main__":
    main()
