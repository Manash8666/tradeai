import json
import re
import logging
import zoneinfo
from datetime import datetime
from typing import Dict, Any, Optional

from backend.app.core.timezone_guards import temporal_guard

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class PineScriptSignalParser:
    """
    Intelligent Parser for unstructured or templated TradingView Pine Script alert strings.
    Extracts dynamic {{strategy.order.action}}, {{close}}, and {{ticker}} parameters,
    normalizes numbers, and evaluates Indian market session validity.
    """

    @staticmethod
    def parse_pine_alert(raw_text: str) -> Dict[str, Any]:
        """
        Parses JSON strings, key-value pairs, or unstructured alert messages sent by Pine Script.
        """
        raw_text = raw_text.strip()

        # 1. Try direct JSON parsing
        if raw_text.startswith("{") and raw_text.endswith("}"):
            try:
                data = json.loads(raw_text)
                return PineScriptSignalParser._normalize_parsed_dict(data)
            except json.JSONDecodeError:
                pass

        # 2. Heuristic regex extraction for common TradingView message templates
        extracted = {}

        # Action: BUY / SELL / LONG / SHORT
        action_match = re.search(r"\b(buy|sell|long|short|close|exit)\b", raw_text, re.IGNORECASE)
        if action_match:
            action_raw = action_match.group(1).upper()
            extracted["action"] = "BUY" if action_raw in ["BUY", "LONG"] else ("SELL" if action_raw in ["SELL", "SHORT"] else "CLOSE")

        # Price extraction: looks for numbers after "price", "@", or standalone floats
        price_match = re.search(r"(?:price|@|close)[:\s]*([0-9]+(?:\.[0-9]+)?)", raw_text, re.IGNORECASE)
        if price_match:
            extracted["price"] = float(price_match.group(1))

        # Ticker extraction: e.g. NSE:NIFTY, NIFTY50, RELIANCE
        ticker_match = re.search(r"\b(?:NSE:|BSE:)?([A-Z0-9_]{3,15})\b", raw_text)
        if ticker_match:
            extracted["ticker"] = ticker_match.group(1).upper()

        return PineScriptSignalParser._normalize_parsed_dict(extracted)

    @staticmethod
    def _normalize_parsed_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures default values and standard Indian schema conformance."""
        now = temporal_guard.get_market_time()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S IST")

        action = str(data.get("action", "HOLD")).upper()
        if action in ["LONG"]:
            action = "BUY"
        elif action in ["SHORT"]:
            action = "SELL"

        ticker = str(data.get("ticker", data.get("symbol", "NIFTY50"))).upper()
        if ":" in ticker:
            ticker = ticker.split(":")[-1]

        price = float(data.get("price", data.get("close", 0.0)))
        timeframe = str(data.get("timeframe", data.get("interval", "5m")))
        strategy = str(data.get("strategy", data.get("strategy_name", "PineStrategy")))

        # Check if trade is arriving during active Indian market hours
        is_market_hours = temporal_guard.is_market_open()

        # Signal quality score
        quality = "HIGH" if price > 0 and action in ["BUY", "SELL"] and ticker else "LOW"

        return {
            "ticker": ticker,
            "action": action,
            "price_inr": price,
            "timeframe": timeframe,
            "strategy": strategy,
            "signal_quality": quality,
            "is_market_hours": is_market_hours,
            "received_at_ist": now_str,
        }
