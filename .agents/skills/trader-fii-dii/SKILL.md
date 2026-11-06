---
name: trader-fii-dii
description: >-
  Institutional Money Tracker (Indian Market). Replaces US Congress disclosures
  by tracking official NSE Foreign Institutional Investor (FII) and Domestic
  Institutional Investor (DII) net cash buy/sell figures, plus daily NSE Bulk
  and Block deals. Evaluates whether big money is injecting or withdrawing capital
  from Indian equities. Writes trader/fiidii.json.
argument-hint: "[flows | deals | summary]"
---

# trader-fii-dii (Institutional Flows)

FIIs (Foreign Institutional Investors) and DIIs (Mutual Funds, LIC, Domestic Institutions)
account for the dominant liquidity in the Indian stock market. Tracking their net flows
provides critical market regime context before entering any day trade.

```bash
python3 "${CLAUDE_SKILL_DIR}/fiidii.py" flows       # Latest FII and DII cash buy/sell totals
python3 "${CLAUDE_SKILL_DIR}/fiidii.py" deals       # Top Bulk and Block deals on NSE
python3 "${CLAUDE_SKILL_DIR}/fiidii.py" summary     # Institutional sentiment report -> trader/fiidii.json
```

## How It Informs Day Trades
* **FII Net Buyers (> ₹1,000 Cr)**: Strong tailwind for Nifty/Bank Nifty long setups and ORB breakouts.
* **FII Net Sellers (> -₹1,000 Cr)**: High risk of gap-down or morning rally exhaustion; favor short setups.
* **Bulk/Block Deals**: Shows which specific institutional funds (e.g. Morgan Stanley, Goldman Sachs, SBI MF) bought or sold large equity blocks.
