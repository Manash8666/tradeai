---
name: trader-analyst
description: >-
  Indian Stock & Liquidity Analyst. Summarizes 52-week price extremes, average daily
  trading volume, valuation context, and price momentum for NSE equities.
  Free public data, zero signup.
argument-hint: "info [--symbol SYMBOL]"
---

# trader-analyst (NSE Stock & Liquidity Facts)

Provides key context on volume, 52-week range proximity, and exchange liquidity
before entering a day trade.

```bash
python3 "${CLAUDE_SKILL_DIR}/facts.py" info --symbol INFY.NS
python3 "${CLAUDE_SKILL_DIR}/facts.py" info --symbol HDFCBANK.NS
```
