---
name: trader-oi
description: >-
  Derivatives & Volatility Intelligence (Indian Market). Computes live
  Put-Call Ratio (PCR), Open Interest (OI) buildup, and India VIX regimes
  for Nifty 50 and Bank Nifty. Informs whether option writers are building
  support or capping rallies. Writes trader/oi.json.
argument-hint: "[vix | pcr | chain | summary] [--symbol NIFTY|BANKNIFTY]"
---

# trader-oi (Open Interest & India VIX)

In the Indian market, 90%+ of total volume is in index derivatives. Even when
trading equity cash, options positioning dictates whether the broader market
will support or reject a breakout.

```bash
python3 "${CLAUDE_SKILL_DIR}/oi.py" vix                  # India VIX volatility regime
python3 "${CLAUDE_SKILL_DIR}/oi.py" pcr --symbol NIFTY   # Put-Call Ratio for Nifty
python3 "${CLAUDE_SKILL_DIR}/oi.py" pcr --symbol BANKNIFTY
python3 "${CLAUDE_SKILL_DIR}/oi.py" summary              # Full derivatives report -> trader/oi.json
```

## Interpretation Rules
* **India VIX < 13**: Quiet market, smaller ranges, higher risk of false breakouts.
* **India VIX 13–17.5**: Sweet spot for 15-min Opening Range Breakouts and momentum.
* **India VIX > 18**: High volatility; reduce position size and trail stops closely.
* **NIFTY PCR > 1.2**: Bullish sentiment (Put writers providing support).
* **NIFTY PCR < 0.8**: Bearish sentiment (Call writers capping the market).
