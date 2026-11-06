---
name: trader-alerts
description: >-
  Price & Time Alerts Monitor (Indian Market). Monitors live prices for active
  trades in trader/trades.json, flags Stop-Loss and Target hits, and sends
  critical Indian session time alerts (09:15 Open, 09:30 ORB completion, 15:10 Squareoff warning).
argument-hint: "[check]"
---

# trader-alerts (Indian Session Price & Time Alerts)

Keeps watch over open positions and market milestones throughout the trading day.

```bash
python3 "${CLAUDE_SKILL_DIR}/alerts.py" check    # Audit live prices and time milestones
```

## Critical Milestones Tracked
* **09:15 IST**: Market open alert.
* **09:30 IST**: 15-min Opening Range completed.
* **15:10 IST**: Pre-squareoff warning (5 minutes before broker auto-close).
* **Target & Stop Triggers**: Real-time notification if any open position reaches target or hits stop.
