#!/usr/bin/env python3
"""Order Ticket & Paper Trading Broker for day-trader-india.
Generates order tickets for Indian discount brokers (Zerodha MIS, Dhan Intraday,
Angel One) and maintains a free local paper trading ledger.
Paper trading by default. Never sends an order without explicit confirmation.

Commands:
    python3 ticket.py preview      # Show order ticket from trader/order.json
    python3 ticket.py paper        # Execute paper trade -> trader/trades.json
    python3 ticket.py pnl          # View active positions and paper trading ledger
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


def cmd_preview():
    trader_dir = get_trader_dir()
    order_path = os.path.join(trader_dir, "order.json")
    if not os.path.exists(order_path):
        print("No order.json found. Run trader-budget first.")
        return

    with open(order_path, "r", encoding="utf-8") as f:
        order = json.load(f)

    print(f"\n{'='*56}\n  INDIAN BROKER ORDER TICKET (MIS / INTRADAY)\n{'='*56}")
    print(f"  Exchange           : NSE")
    print(f"  Symbol             : {order['symbol']}")
    print(f"  Action             : {'BUY' if order['direction'] == 'LONG' else 'SELL'}")
    print(f"  Order Type         : LIMIT (Bracket / Cover Order)")
    print(f"  Product Code       : MIS (Intraday with 5x leverage)")
    print(f"  Quantity           : {order['quantity']} shares")
    print(f"  Entry Limit Price  : ₹{order['entry_price']}")
    print(f"  Stop-Loss Trigger  : ₹{order['stop_loss']}")
    print(f"  Target Price       : ₹{order['target']}")
    print(f"  Total Margin Block : ₹{order['margin_required_inr']:,}")
    print(f"  Max Rupee Risk     : ₹{order['max_risk_inr']:,}")
    print(f"{'='*56}")
    print("Mode: PAPER TRADING (Safe simulation). Run 'python3 ticket.py paper' to fill.\n")


def cmd_paper():
    trader_dir = get_trader_dir()
    order_path = os.path.join(trader_dir, "order.json")
    if not os.path.exists(order_path):
        print("No order.json found. Run trader-budget first.")
        return

    with open(order_path, "r", encoding="utf-8") as f:
        order = json.load(f)

    now_ist = datetime.now(timezone.utc).astimezone(IST)
    trade_entry = {
        "id": f"TRD-{int(time.time())}",
        "timestamp": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        "symbol": order["symbol"],
        "direction": order["direction"],
        "quantity": order["quantity"],
        "entry_price": order["entry_price"],
        "stop_loss": order["stop_loss"],
        "target": order["target"],
        "margin_blocked": order["margin_required_inr"],
        "status": "OPEN",
        "current_pnl_inr": 0.0
    }

    trades_file = os.path.join(trader_dir, "trades.json")
    trades = []
    if os.path.exists(trades_file):
        with open(trades_file, "r", encoding="utf-8") as f:
            trades = json.load(f)

    trades.append(trade_entry)
    with open(trades_file, "w", encoding="utf-8") as f:
        json.dump(trades, f, indent=2)

    print(f"  🎉 [Paper Execution Filled]")
    print(f"  Position ID : {trade_entry['id']}")
    print(f"  Bought {order['quantity']} {order['symbol']} @ ₹{order['entry_price']}")
    print(f"  Stop: ₹{order['stop_loss']} | Target: ₹{order['target']}")
    print(f"  Logged to {trades_file}\n")


def get_live_price(symbol):
    try:
        encoded = urllib.parse.quote(symbol)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval=1m&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            meta = data["chart"]["result"][0]["meta"]
            return meta.get("regularMarketPrice")
    except Exception:
        return None


def cmd_pnl():
    trader_dir = get_trader_dir()
    trades_file = os.path.join(trader_dir, "trades.json")
    if not os.path.exists(trades_file):
        print("No paper trades executed yet.")
        return

    with open(trades_file, "r", encoding="utf-8") as f:
        trades = json.load(f)

    if not trades:
        print("No paper trades executed yet.")
        return

    print(f"\n{'='*72}\n  PAPER TRADING PORTFOLIO & REAL-TIME INTRADAY LEDGER\n{'='*72}")
    total_unrealized = 0.0
    for t in trades:
        sym = t["symbol"]
        qty = t["quantity"]
        entry = t["entry_price"]
        direction = t.get("direction", "LONG")
        status = t.get("status", "OPEN")

        curr_price = get_live_price(sym) if status == "OPEN" else None
        price_display = f"₹{curr_price:.2f}" if curr_price is not None else "N/A"

        pnl_str = ""
        if curr_price is not None and status == "OPEN":
            diff = (curr_price - entry) if direction == "LONG" else (entry - curr_price)
            unrealized = diff * qty
            pct = (diff / entry) * 100 if entry else 0.0
            total_unrealized += unrealized
            tag = "🟢 PROFIT" if unrealized >= 0 else "🔴 LOSS"
            sign = "+" if unrealized >= 0 else ""
            pnl_str = f" | Live P&L: {sign}₹{unrealized:,.2f} ({sign}{pct:.2f}%) [{tag}]"

        print(f"  [{t['id']}] {sym:12} {direction:5} | {qty:4d} shs @ ₹{entry:.2f} -> Now: {price_display}{pnl_str}")
        print(f"    Stop: ₹{t['stop_loss']} | Target: ₹{t['target']} | Status: {status}")

    sign_tot = "+" if total_unrealized >= 0 else ""
    tot_tag = "🟢 IN PROFIT" if total_unrealized >= 0 else "🔴 IN LOSS"
    print(f"  ----------------------------------------------------------------------")
    print(f"  Total Active Portfolio P&L: {sign_tot}₹{total_unrealized:,.2f} [{tot_tag}]")
    print(f"{'='*72}\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "preview"
    if cmd in ("preview", "ticket", "order", "show"):
        cmd_preview()
    elif cmd in ("paper", "execute", "buy", "fill"):
        cmd_paper()
    elif cmd in ("pnl", "ledger", "positions", "portfolio"):
        cmd_pnl()
    else:
        print(f"Unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
