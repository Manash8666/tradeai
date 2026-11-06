#!/usr/bin/env python3
"""FII / DII & Institutional Deal Intelligence for day-trader-india.
Fetches official NSE daily Foreign & Domestic Institutional cash flows
and Bulk / Block deals using free public endpoints. No API keys required.

Commands:
    python3 fiidii.py flows       # Latest FII and DII net cash buy/sell figures
    python3 fiidii.py deals       # Today's NSE Bulk & Block deals
    python3 fiidii.py summary     # Combined institutional sentiment -> trader/fiidii.json
"""

import json
import os
import subprocess
import sys
import time

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


def nse_curl(url, referer="https://www.nseindia.com/"):
    """Fetch an NSE endpoint using curl with cookie handling."""
    cookie_file = "/tmp/nse_fii_cookie.txt"
    # Ensure fresh cookies from homepage if cookie file is older than 10 mins
    if not os.path.exists(cookie_file) or (time.time() - os.path.getmtime(cookie_file) > 600):
        init_cmd = [
            "curl", "-s", "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "-c", cookie_file, "https://www.nseindia.com/"
        ]
        subprocess.run(init_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        time.sleep(0.5)

    cmd = [
        "curl", "-s", "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "-b", cookie_file, "-e", referer, url
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
    if res.returncode != 0:
        raise RuntimeError(f"curl failed: {res.stderr}")
    return json.loads(res.stdout)


def get_flows():
    """Fetch daily FII and DII net cash figures from NSE."""
    url = "https://www.nseindia.com/api/fiidiiTradeReact"
    data = nse_curl(url, referer="https://www.nseindia.com/")
    return data


def get_deals():
    """Fetch Bulk and Block deals from NSE."""
    url = "https://www.nseindia.com/api/snapshot-capital-market-largedeal"
    data = nse_curl(url, referer="https://www.nseindia.com/market-data/large-deals")
    return data


def cmd_flows():
    print(f"\n{'='*56}\n  NSE FII & DII NET INSTITUTIONAL CASH ACTIVITY\n{'='*56}")
    try:
        flows = get_flows()
        for row in flows:
            cat = row.get("category", "")
            date = row.get("date", "")
            buy = float(row.get("buyValue", 0))
            sell = float(row.get("sellValue", 0))
            net = float(row.get("netValue", 0))
            sign = "+" if net > 0 else ""
            status = "🟢 NET BUYER" if net > 0 else "🔴 NET SELLER"
            print(f"  Category: {cat:<8} | Date: {date}")
            print(f"  Buy: ₹{buy:>9.2f} Cr  | Sell: ₹{sell:>9.2f} Cr | Net: {sign}₹{net:>9.2f} Cr  [{status}]\n")
    except Exception as e:
        print(f"  Failed to fetch FII/DII flows: {e}")
    print(f"{'='*56}\n")


def cmd_deals():
    print(f"\n{'='*64}\n  NSE BULK & BLOCK DEALS (INSTITUTIONAL POSITIONING)\n{'='*64}")
    try:
        raw = get_deals()
        as_on = raw.get("as_on_date", "Today")
        bulk = raw.get("BULK_DEALS_DATA", [])
        block = raw.get("BLOCK_DEALS_DATA", [])
        print(f"  As on Date: {as_on}\n")

        if bulk:
            print(f"  --- TOP BULK DEALS ({len(bulk)} total) ---")
            for d in bulk[:8]:
                sym = d.get("symbol", "")
                client = d.get("clientName", "")[:26]
                side = d.get("buySell", "")
                qty = d.get("qty", "")
                price = d.get("watp", d.get("tradePrice", ""))
                side_tag = "🟢 BUY" if side.upper() == "BUY" else "🔴 SELL"
                print(f"  {sym:<12} {side_tag} | {client:<26} | Qty: {qty:>8} @ ₹{price}")
            print()

        if block:
            print(f"  --- TOP BLOCK DEALS ({len(block)} total) ---")
            for d in block[:8]:
                sym = d.get("symbol", "")
                client = d.get("clientName", "")[:26]
                side = d.get("buySell", "")
                qty = d.get("qty", "")
                price = d.get("watp", d.get("tradePrice", ""))
                side_tag = "🟢 BUY" if side.upper() == "BUY" else "🔴 SELL"
                print(f"  {sym:<12} {side_tag} | {client:<26} | Qty: {qty:>8} @ ₹{price}")
            print()

        if not bulk and not block:
            print("  No bulk/block deals reported yet for this session.")
    except Exception as e:
        print(f"  Failed to fetch deals: {e}")
    print(f"{'='*64}\n")


def cmd_summary():
    ensure_trader_dir()
    summary = {
        "timestamp": time.time(),
        "fii_dii": [],
        "bulk_deals": [],
        "sentiment": "NEUTRAL"
    }
    try:
        flows = get_flows()
        summary["fii_dii"] = flows
        fii_net = 0.0
        dii_net = 0.0
        for row in flows:
            cat = row.get("category", "")
            net = float(row.get("netValue", 0))
            if "FII" in cat:
                fii_net = net
            elif "DII" in cat:
                dii_net = net

        total_net = fii_net + dii_net
        if total_net > 1000:
            summary["sentiment"] = "STRONG_BULLISH"
        elif total_net > 200:
            summary["sentiment"] = "BULLISH"
        elif total_net < -1000:
            summary["sentiment"] = "STRONG_BEARISH"
        elif total_net < -200:
            summary["sentiment"] = "BEARISH"
        else:
            summary["sentiment"] = "NEUTRAL"
    except Exception as e:
        print(f"Notice: FII/DII flow warning ({e})")

    try:
        deals = get_deals()
        summary["bulk_deals"] = deals.get("BULK_DEALS_DATA", [])[:15]
    except Exception as e:
        print(f"Notice: Large deals warning ({e})")

    trader_dir = get_trader_dir()
    out_file = os.path.join(trader_dir, "fiidii.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[FII/DII Summary] Institutional Sentiment: {summary['sentiment']}")
    print(f"Saved report to {out_file}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "flows"
    if cmd in ("flows", "fii", "dii", "cash", "institutional"):
        cmd_flows()
    elif cmd in ("deals", "bulk", "block", "large"):
        cmd_deals()
    elif cmd in ("summary", "overview", "sentiment"):
        cmd_summary()
    else:
        print(f"Unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
