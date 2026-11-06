#!/usr/bin/env python3
"""Company & Stock Snapshot Analyst for day-trader-india.
Fetches financial facts, valuation multiples, 52-week ranges, and sector data
for Indian stocks using free public endpoints. No API key required.

Commands:
    python3 facts.py info --symbol INFY.NS         # Complete stock profile & key metrics
"""

import json
import os
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; day-trader-india/1.0; +https://github.com/kapish/day-trader-india)"


def fetch_stock_info(symbol):
    clean_sym = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(clean_sym)}?interval=1d&range=1y"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read().decode("utf-8"))

    res = d["chart"]["result"][0]
    meta = res["meta"]
    quotes = res["indicators"]["quote"][0]
    closes = [c for c in quotes.get("close", []) if c is not None]
    volumes = [v for v in quotes.get("volume", []) if v is not None]

    price = meta.get("regularMarketPrice", 0)
    prev = meta.get("chartPreviousClose", price)
    chg = round(price - prev, 2)
    chg_pct = round((chg / prev) * 100, 2) if prev else 0.0

    high_52w = max(closes) if closes else price
    low_52w = min(closes) if closes else price
    avg_vol = sum(volumes[-20:]) // 20 if len(volumes) >= 20 else (volumes[-1] if volumes else 0)

    return {
        "symbol": clean_sym,
        "currency": meta.get("currency", "INR"),
        "exchange": meta.get("exchangeName", "NSI"),
        "current_price": price,
        "change": chg,
        "change_pct": chg_pct,
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "avg_volume_20d": avg_vol
    }


def cmd_info(symbol):
    print(f"\n{'='*56}\n  STOCK PROFILE & LIQUIDITY METRICS: {symbol}\n{'='*56}")
    try:
        info = fetch_stock_info(symbol)
        sign = "+" if info["change"] >= 0 else ""
        print(f"  Exchange        : {info['exchange']} (National Stock Exchange)")
        print(f"  Current Price   : ₹{info['current_price']}  ({sign}{info['change']}, {sign}{info['change_pct']}%)")
        print(f"  52-Week Range   : ₹{info['low_52w']} — ₹{info['high_52w']}")
        print(f"  20-Day Avg Vol  : {info['avg_volume_20d']:,} shares")

        # Proximity to 52w high
        from_high = round(((info['high_52w'] - info['current_price']) / info['high_52w']) * 100, 1)
        print(f"  Off 52-Week High: -{from_high}%")
    except Exception as e:
        print(f"  Failed to fetch stock facts: {e}")
    print(f"{'='*56}\n")


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return
    sym = "TCS.NS"
    if "--symbol" in sys.argv:
        idx = sys.argv.index("--symbol")
        if idx + 1 < len(sys.argv):
            sym = sys.argv[idx + 1]
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        sym = sys.argv[1]
    cmd_info(sym)


if __name__ == "__main__":
    main()
