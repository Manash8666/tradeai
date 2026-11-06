---
name: trader-broker
description: >-
  Indian Broker Order Ticket & Paper Simulator. Generates ready-to-execute
  MIS intraday bracket orders matching Indian discount broker interfaces
  (Zerodha Kite, Dhan, Angel One). Maintains a local paper trading ledger in
  trader/trades.json. Paper trading by default.
argument-hint: "[preview | paper | pnl]"
---

# trader-broker (Order Ticket & Paper Simulator)

Executes paper trades with zero risk and zero broker credentials required. Formats
standard Indian intraday MIS bracket tickets.

```bash
python3 "${CLAUDE_SKILL_DIR}/ticket.py" preview    # Review trade ticket from trader/order.json
python3 "${CLAUDE_SKILL_DIR}/ticket.py" paper      # Execute safe paper trade -> trader/trades.json
python3 "${CLAUDE_SKILL_DIR}/ticket.py" pnl        # View paper trading portfolio and ledger
```

## Features
* **Safety First**: Paper trading is the default. No real orders are placed.
* **Format**: Generates standard Indian exchange tickets (Product: MIS, Order: LIMIT/SL-M).
* **Ledger**: Tracks open and closed positions in `trader/trades.json`.
