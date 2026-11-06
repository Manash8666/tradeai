---
name: trader-scanner
description: >-
  Indian Market Chart Scanner. Scans liquid NSE stocks (Nifty 50, Nifty 100, F&O)
  for high-probability intraday setups: 15-minute Opening Range Breakouts (ORB),
  20-day high breakouts, bull flags, 20-SMA reclaims, and oversold bounces.
  Pre-market scan (before 09:15 IST) and live intraday scan (09:30–15:15 IST).
  Writes trader/watchlist.json and trader/orb_candidates.json. Free public data,
  no API key required. Use when the user says "scan the Indian market", "scan NSE",
  "find me Nifty setups", "opening range breakout NSE", "what is breaking out today",
  or "pre-market scan India".
argument-hint: "[universe | daily | orb | indices]"
---

# trader-scanner (Indian Market Edition)

The Chart Scanner is the first step of an Indian market day trade. It scans liquid
NSE-listed equities and indices, filtering out illiquid stocks and circuit-locked
names to find setups matching tested rules.

`${CLAUDE_SKILL_DIR}` below is this skill's folder.

```bash
python3 "${CLAUDE_SKILL_DIR}/scan.py" universe       # -> downloads NSE Nifty 100 universe to trader/universe.txt
python3 "${CLAUDE_SKILL_DIR}/scan.py" indices        # -> live benchmark snapshot (Nifty 50, Bank Nifty, VIX, Sensex)
python3 "${CLAUDE_SKILL_DIR}/scan.py" daily          # before 09:15 IST: daily setups -> trader/watchlist.json
python3 "${CLAUDE_SKILL_DIR}/scan.py" orb            # after 09:30 IST: 15-min Opening Range Breakouts -> trader/orb_candidates.json
```

## Market Timings (IST)
* **09:00 – 09:08 IST**: Pre-open price discovery.
* **09:15 IST**: Normal market open.
* **09:15 – 09:30 IST**: Opening Range formation (first three 5-min bars).
* **09:30 – 10:30 IST**: Prime morning ORB execution window.
* **13:00 – 14:00 IST**: European markets open (FTSE/DAX catalyst for Nifty/Bank Nifty).
* **15:15 IST**: Hard stop / square-off cutoff before broker auto-squareoff.

## Files Read and Written
* `trader/universe.txt`: List of liquid NSE stock tickers (`.NS`).
* `trader/watchlist.json`: Daily candidate setups identified before the bell.
* `trader/orb_candidates.json`: Live 15-minute Opening Range Breakouts.
