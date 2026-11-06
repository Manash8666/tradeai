---
name: trader-exit
description: >-
  Intraday Exit Planner (Indian Market). Sets Stop-Loss and multi-stage Take-Profit
  targets (1:1.5R and 1:2R) before entering a trade. Enforces a mandatory hard stop
  at 15:15 IST to prevent Indian broker auto-squareoff penalties.
  Reads trader/setup.json and writes trader/plan.json.
argument-hint: "[plan]"
---

# trader-exit (NSE Exit & Auto-Squareoff Planner)

In day trading, your exit plan must be defined before you enter. This skill calculates
stop levels based on the Opening Range structure and enforces the Indian market's
strict intraday timing rules.

```bash
python3 "${CLAUDE_SKILL_DIR}/exit.py" plan     # Plan exit levels from trader/setup.json -> trader/plan.json
```

## Rules & Disciplines
* **Stop-Loss**: Placed at the Opening Range Midpoint (or Range Low/High) to ensure reasonable risk.
* **Risk-Reward (RR)**: Generates 1:1.5R and 1:2.0R profit targets.
* **Mandatory 15:15 IST Hard Stop**: In India, brokers (Zerodha, Angel One, Groww, Upstox) begin auto-squaring off MIS intraday positions between 15:15 and 15:25 IST, charging a penalty fee of ₹50 + 18% GST per order. All intraday positions must be closed by 15:15 IST win or lose.
