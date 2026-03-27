"""
YFinance Adapter (Global Macro Data)
=====================================
Fetches daily data for global macros required by the Orchestrator's
Causality and Risk Parity engines (S&P 500, Crude, USD/INR, VIX).
"""

import logging
from typing import Dict, Any

import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


class YFinanceAdapter:
    """Retrieves EOD / Global Macro data asynchronously."""

    # Ticker definitions mapping global macros to yfinance symbols
    MACROS = {
        "india_vix": "^INDIAVIX",
        "crude_oil": "CL=F",
        "usd_inr": "INR=X",
        "us_10y_yield": "^TNX",
        "sp500": "^GSPC",
    }

    def __init__(self):
        logger.info("YFinanceAdapter initialized.")

    async def fetch_macro_snapshot(self) -> Dict[str, Any]:
        """
        Pulls down the latest daily change % for the configured global macros.
        """
        snapshot = {}
        for name, symbol in self.MACROS.items():
            try:
                # Retrieve last 2 days of data to compute the % change
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")  # Pad for weekends/holidays

                if len(hist) >= 2:
                    last_close = hist["Close"].iloc[-1]
                    prev_close = hist["Close"].iloc[-2]
                    change_pct = (last_close - prev_close) / prev_close

                    snapshot[f"{name}_close"] = float(last_close)
                    snapshot[f"{name}_change_pct"] = float(change_pct)

            except Exception as exc:
                logger.warning(f"yfinance failed to retrieve {name} ({symbol}): {exc}")

        return snapshot
