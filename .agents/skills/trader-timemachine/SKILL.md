---
name: trader-timemachine
description: >-
  Trade Outcome Simulator (Indian Market). Runs 10,000 Monte Carlo replays of the
  remaining intraday session using the stock's actual 5-minute candle distributions.
  Reports win rate, stop rate, and honest Expected Value (EV) before you risk real money.
  Reads trader/plan.json and writes trader/timemachine.json.
argument-hint: "[replay] [--runs 10000]"
---

# trader-timemachine (Monte Carlo Trade Simulator)

Before risking a single rupee, the Time Machine simulates the rest of the day
10,000 times, drawing from the stock's own recent 5-minute session bars.

```bash
python3 "${CLAUDE_SKILL_DIR}/timemachine.py" replay               # 10,000 iterations to 15:15 IST
python3 "${CLAUDE_SKILL_DIR}/timemachine.py" replay --runs 5000   # Fast 5,000 run replay
```

## Why This Matters
* A 1:1.5R trade with a 40% win rate and 40% stop rate has positive Expected Value ($+₹0.19$ per ₹1 risked) because of the asymmetric payoff.
* If a trade exhibits negative Expected Value (e.g. EV $< 0$), the tool flags it as **UNFAVORABLE**, preventing you from entering a losing mathematical proposition.
