#!/usr/bin/env python3
"""Risk & Compliance Guard for day-trader-india.
Checks every proposed trade against Indian regulatory limits, transaction taxes
(STT, GST, Exchange charges, Stamp duty), risk ceilings, and time windows.

Commands:
    python3 check.py check                     # Check trader/order.json against risk rules
    python3 check.py charges --val 100000      # Breakdown of Indian transaction charges
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

BROKERAGE_PER_ORDER = 20.0  # Discount broker standard (₹20 per executed order)
STT_RATE_SELL = 0.00025     # 0.025% on equity intraday sell turnover
EXCHANGE_RATE = 0.0000345   # 0.00345% NSE turnover charge
SEBI_RATE = 0.000001        # ₹10 per crore
STAMP_DUTY_BUY = 0.00003    # 0.003% on buy turnover
GST_RATE = 0.18             # 18% on (brokerage + exchange charges + sebi fees)


def get_trader_dir():
    if "TRADER_DIR" in os.environ:
        return os.environ["TRADER_DIR"]
    if os.path.exists("trader"):
        return "trader"
    elif os.path.exists("../trader"):
        return "../trader"
    return "trader"


def calculate_indian_charges(buy_value, sell_value):
    turnover = buy_value + sell_value
    brokerage = BROKERAGE_PER_ORDER * 2.0  # Buy order + Sell order
    stt = round(sell_value * STT_RATE_SELL, 2)
    exchange_charges = round(turnover * EXCHANGE_RATE, 2)
    sebi_charges = round(turnover * SEBI_RATE, 2)
    stamp_duty = round(buy_value * STAMP_DUTY_BUY, 2)
    gst = round((brokerage + exchange_charges + sebi_charges) * GST_RATE, 2)

    total_charges = round(brokerage + stt + exchange_charges + sebi_charges + stamp_duty + gst, 2)
    return {
        "brokerage": brokerage,
        "stt": stt,
        "exchange_charges": exchange_charges,
        "sebi_charges": sebi_charges,
        "stamp_duty": stamp_duty,
        "gst": gst,
        "total_charges": total_charges,
        "breakeven_points_per_share": 0.0
    }


def cmd_check():
    trader_dir = get_trader_dir()
    order_path = os.path.join(trader_dir, "order.json")
    if not os.path.exists(order_path):
        print("No order.json found. Run trader-budget first.")
        return

    with open(order_path, "r", encoding="utf-8") as f:
        order = json.load(f)

    qty = order["quantity"]
    entry = order["entry_price"]
    target = order["target"]
    stop = order["stop_loss"]
    direction = order.get("direction", "LONG")

    buy_val = qty * entry if direction == "LONG" else qty * target
    sell_val = qty * target if direction == "LONG" else qty * entry

    charges = calculate_indian_charges(buy_val, sell_val)
    charges["breakeven_points_per_share"] = round(charges["total_charges"] / qty, 2)

    now_ist = datetime.now(timezone.utc).astimezone(IST)
    current_time_str = now_ist.strftime("%H:%M")

    violations = []

    # 1. Margin Limit Check
    if order["margin_utilization_pct"] > 80.0:
        violations.append(f"Margin utilization ({order['margin_utilization_pct']}%) exceeds safe 80% capital ceiling")

    # 2. Time Window Check (Block fresh entries after 14:30 IST)
    hour = now_ist.hour
    minute = now_ist.minute
    if hour > 14 or (hour == 14 and minute > 30):
        violations.append(f"Time {current_time_str} IST is past the 14:30 IST entry cutoff (auto-squareoff at 15:15)")

    # 3. Minimum Profit vs Charges check
    net_profit = order["potential_profit_inr"] - charges["total_charges"]
    if net_profit <= charges["total_charges"]:
        violations.append(f"Estimated profit (₹{order['potential_profit_inr']}) is too close to transaction charges (₹{charges['total_charges']})")

    passed = len(violations) == 0

    print(f"\n{'='*56}\n  SEBI RISK & TRANSACTION CHARGES AUDIT\n{'='*56}")
    print(f"  Trade Verdict     : [{'PASS - APPROVED' if passed else 'BLOCK - REFUSED'}]")
    print(f"  Estimated Charges : ₹{charges['total_charges']} total")
    print(f"    • Brokerage     : ₹{charges['brokerage']}")
    print(f"    • STT (Tax)     : ₹{charges['stt']}")
    print(f"    • Exchange / GST: ₹{round(charges['exchange_charges'] + charges['gst'], 2)}")
    print(f"    • Stamp Duty    : ₹{charges['stamp_duty']}")
    print(f"  Breakeven Spread  : ₹{charges['breakeven_points_per_share']} / share")
    print(f"  Net Target Profit : ₹{round(net_profit, 2)} (after all taxes & brokerage)")

    if violations:
        print("\n  VIOLATIONS / RISKS DETECTED:")
        for v in violations:
            print(f"    ❌ {v}")
    print(f"{'='*56}\n")

    return 0 if passed else 1


def cmd_charges(trade_value):
    """Breakdown of Indian transaction charges for an intraday round trip."""
    buy_value = trade_value
    sell_value = trade_value
    charges = calculate_indian_charges(buy_value, sell_value)
    turnover = buy_value + sell_value
    print(f"\n{'='*56}\n  INDIAN TRANSACTION CHARGES (INTRADAY ROUND-TRIP)\n{'='*56}")
    print(f"  Trade Value (Each Leg) : ₹{trade_value:,.2f}")
    print(f"  Total Turnover (2 Legs): ₹{turnover:,.2f}")
    print(f"  --------------------------------------------------------")
    print(f"  Brokerage (₹20 x 2)    : ₹{charges['brokerage']:.2f}")
    print(f"  STT (0.025% on Sell)   : ₹{charges['stt']:.2f}")
    print(f"  Exchange Charges       : ₹{charges['exchange_charges']:.2f}")
    print(f"  SEBI Turnover Fees     : ₹{charges['sebi_charges']:.2f}")
    print(f"  Stamp Duty (0.003% Buy): ₹{charges['stamp_duty']:.2f}")
    print(f"  GST (18% on fees)      : ₹{charges['gst']:.2f}")
    print(f"  --------------------------------------------------------")
    print(f"  TOTAL CHARGES & TAXES  : ₹{charges['total_charges']:.2f}  ({(charges['total_charges'] / turnover) * 100:.3f}% of turnover)")
    print(f"{'='*56}\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "check"
    if cmd in ("check", "audit", "verify", "validate"):
        sys.exit(cmd_check())
    elif cmd in ("charges", "fees", "tax", "breakdown"):
        val = 100000.0
        if "--val" in sys.argv:
            idx = sys.argv.index("--val")
            if idx + 1 < len(sys.argv):
                try:
                    val = float(sys.argv[idx + 1])
                except ValueError:
                    val = 100000.0
        elif len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
            try:
                val = float(sys.argv[2])
            except ValueError:
                val = 100000.0
        cmd_charges(val)
    else:
        print(f"Unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
