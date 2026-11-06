---
name: trader-news
description: >-
  Indian Market News Monitor. Tracks real-time breaking catalysts, RBI policy
  updates, earnings announcements, and corporate news for Indian equities and
  indices. Filters noise and flags market-moving events for watchlist stocks.
  Writes trader/news.json.
argument-hint: "[market | symbol --symbol SYMBOL | monitor]"
---

# trader-news (Indian Market News Monitor)

Headlines drive opening gaps and sudden midday reversals on Dalal Street. This skill
tracks breaking stories from Economic Times, Moneycontrol, Livemint, BusinessLine,
and NDTV Profit.

```bash
python3 "${CLAUDE_SKILL_DIR}/news.py" market                  # Live macro & market-wide headlines
python3 "${CLAUDE_SKILL_DIR}/news.py" symbol --symbol RELIANCE # Specific stock headlines & catalysts
python3 "${CLAUDE_SKILL_DIR}/news.py" monitor                 # Batch scan for all watchlist stocks -> trader/news.json
```

## How It Informs Day Trades
* Never trade an Opening Range Breakout into an imminent RBI interest rate announcement or unreleased earnings report.
* A breakout accompanied by positive corporate news (order win, earnings beat) has significantly higher follow-through than a low-volume technical drift.
