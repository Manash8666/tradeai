---
name: trader-budget
description: >-
  Position Sizer & Budget Manager (Indian Market). Sizes trade quantities in
  Indian Rupees (₹) based on max risk per trade and calculates upfront capital
  required under SEBI's 5x MIS intraday margin limit.
  Reads trader/plan.json and writes trader/order.json.
argument-hint: "[size] [--risk 1000] [--capital 50000]"
---

# trader-budget (INR Position Sizer)

Sizes every trade to your exact rupee risk budget. It prevents overleveraging
by calculating the exact share count and margin requirement under SEBI regulations.

```bash
python3 "${CLAUDE_SKILL_DIR}/size.py" size --risk 1500 --capital 100000 # Specify risk and total capital
python3 "${CLAUDE_SKILL_DIR}/size.py" size                             # Default: ₹1,000 risk, ₹50,000 capital
```

## Calculations
* **Quantity**: $\lfloor \text{Max Rupee Risk} / \text{Risk Per Share} \rfloor$.
* **Margin Required**: Total Trade Value / 5 (SEBI 20% upfront intraday margin).
* **Margin Utilization**: Warns if required margin exceeds your available cash.
