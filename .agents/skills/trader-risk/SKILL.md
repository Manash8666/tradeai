---
name: trader-risk
description: >-
  Indian Market Risk & Compliance Guard. Audits every trade against SEBI margin
  rules, exact statutory transaction taxes (STT, GST, Exchange turnover fees,
  Stamp duty), maximum capital utilization, and entry timing cutoffs (14:30 IST).
  Reads trader/order.json and yields a strict PASS or BLOCK verdict.
argument-hint: "[check]"
---

# trader-risk (SEBI Compliance & Transaction Tax Guard)

Small profits in day trading can easily be erased by Indian taxes and brokerage
fees. This skill audits your trade ticket and confirms that potential reward
comfortably exceeds all transaction costs and regulatory constraints.

```bash
python3 "${CLAUDE_SKILL_DIR}/check.py" check    # Audit trader/order.json
```

## Checks Performed
1. **Time Window**: Blocks entries initiated after 14:30 IST. Entering within 45 minutes of broker auto-squareoff leaves inadequate time for trade maturation.
2. **Margin Utilization**: Caps required margin at 80% of available trading capital.
3. **Statutory Tax Breakdown**:
   * **STT**: 0.025% on sell turnover.
   * **Exchange Turnover Fee**: 0.00345% of total turnover.
   * **GST**: 18% on brokerage and exchange charges.
   * **Stamp Duty**: 0.003% on buy turnover.
   * **Brokerage**: Standard ₹20 per executed order.
4. **Breakeven Spread**: Calculates exact rupee-per-share gain needed just to cover charges.
