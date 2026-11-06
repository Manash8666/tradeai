#!/usr/bin/env python3
"""Indian Financial News & Breaking Catalysts for day-trader-india.
Fetches real-time market headlines and symbol-specific news using free RSS feeds.
No API key required.

Commands:
    python3 news.py market                 # Breaking Indian market headlines
    python3 news.py symbol --symbol TCS    # News for a specific stock (e.g. TCS, RELIANCE)
    python3 news.py monitor                # News on all stocks in trader/watchlist.json
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (compatible; day-trader-india/1.0; +https://github.com/kapish/day-trader-india)"
def get_trader_dir():
    if "TRADER_DIR" in os.environ:
        return os.environ["TRADER_DIR"]
    if os.path.exists("trader"):
        return "trader"
    elif os.path.exists("../trader"):
        return "../trader"
    return "trader"


def ensure_trader_dir():
    os.makedirs(get_trader_dir(), exist_ok=True)


def fetch_rss(query, limit=10):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        xml_data = resp.read()
    root = ET.fromstring(xml_data)
    items = root.findall(".//item")
    results = []
    for it in items[:limit]:
        title = it.find("title").text if it.find("title") is not None else ""
        link = it.find("link").text if it.find("link") is not None else ""
        pub_date = it.find("pubDate").text if it.find("pubDate") is not None else ""
        source = it.find("source").text if it.find("source") is not None else "Financial News"
        results.append({
            "title": title,
            "link": link,
            "published": pub_date,
            "source": source
        })
    return results


def cmd_market():
    print(f"\n{'='*64}\n  BREAKING INDIAN MARKET HEADLINES (NSE / SENSEX / ECONOMY)\n{'='*64}")
    stories = fetch_rss("NIFTY OR SENSEX OR stock market India", limit=8)
    for idx, s in enumerate(stories, start=1):
        print(f" {idx:2d}. {s['title']}")
        print(f"     Source: {s['source']} | Date: {s['published'][:16]}\n")
    print(f"{'='*64}\n")


def cmd_symbol(symbol):
    clean_sym = symbol.replace(".NS", "").replace(".BO", "")
    print(f"\n{'='*64}\n  CATALYSTS & HEADLINES FOR: {clean_sym}\n{'='*64}")
    stories = fetch_rss(f"{clean_sym} NSE stock share price", limit=6)
    if not stories:
        print("  No breaking headlines found.")
    for idx, s in enumerate(stories, start=1):
        print(f" {idx:2d}. {s['title']}")
        print(f"     Source: {s['source']} | Date: {s['published'][:16]}\n")
    print(f"{'='*64}\n")


def cmd_monitor():
    ensure_trader_dir()
    trader_dir = get_trader_dir()
    wl_path = os.path.join(trader_dir, "watchlist.json")
    symbols = []
    if os.path.exists(wl_path):
        with open(wl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            symbols = [d["symbol"] for d in data][:8]
    if not symbols:
        symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"]

    print(f"[News Monitor] Scanning catalysts for {len(symbols)} watchlist stocks...")
    news_map = {}
    for sym in symbols:
        clean = sym.replace(".NS", "")
        stories = fetch_rss(f"{clean} NSE stock", limit=3)
        news_map[sym] = stories
        time.sleep(0.2)

    out_file = os.path.join(trader_dir, "news.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(news_map, f, indent=2)
    print(f"Saved monitored headlines to {out_file}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "market"
    if cmd in ("market", "top", "headlines", "latest"):
        cmd_market()
    elif cmd in ("symbol", "stock"):
        sym = "NIFTY"
        if "--symbol" in sys.argv:
            idx = sys.argv.index("--symbol")
            if idx + 1 < len(sys.argv):
                sym = sys.argv[idx + 1]
        elif len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
            sym = sys.argv[2]
        cmd_symbol(sym)
    elif cmd in ("monitor", "watchlist"):
        cmd_monitor()
    elif not cmd.startswith("-"):
        cmd_symbol(cmd)
    else:
        print(f"Unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
