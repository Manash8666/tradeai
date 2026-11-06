---
name: trader-entry
description: >-
  Intraday Entry Timer (Indian Market). Monitors 5-minute bars in real time to time
  the exact entry after the 15-minute Opening Range (09:15–09:30 IST). Confirms
  breakout closes above range high with VWAP alignment and volume surge.
  Writes trader/setup.json for trader-exit and trader-timemachine.
argument-hint: "[watch --symbol SYMBOL | check]"
---

# trader-entry (NSE Entry Timer)

The Entry Timer watches a candidate bar by bar. It avoids guessing or chasing
wicks by requiring a completed 5-minute bar close beyond the opening range.

```bash
python3 "${CLAUDE_SKILL_DIR}/entry.py" watch --symbol RELIANCE.NS  # Bar-by-bar monitor for one stock
python3 "${CLAUDE_SKILL_DIR}/entry.py" check                       # Check all candidates in trader/orb_candidates.json
```

## Trigger Rules
* **Long Entry**: First 5-minute candle closing above the 09:15–09:30 Opening Range High.
* **Short Entry**: First 5-minute candle closing below the 09:15–09:30 Opening Range Low.
* **Confirmation Filters**:
  * Price above intraday VWAP for Longs; below VWAP for Shorts.
  * Volume on breakout candle $\ge 1.1\times$ the session average.
* **Output**: Writes `trader/setup.json` consumed by `trader-exit` and `trader-budget`.
