"""
Causality Engine (Predictive Causality)
========================================
Maps Global Macro Events (S&P 500, Nasdaq, Crude, USD/INR) to specific
Indian sectors and stocks.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class CausalityEngine:
    """Predicts downstream effects of global macro trends on Indian equities."""

    def __init__(self):
        # Known causal links (highly simplified for the orchestrator proof-of-concept).
        # In production this requires complex Granger causality testing.
        self._rules = {
            "CRUDE_OIL": {
                "inverse": ["ASIANPAINT.NS", "INDIGO.NS"],  # Paints/Airlines hurt by high oil
                "direct": ["ONGC.NS", "RELIANCE.NS"],  # Upstream producers benefit
            },
            "USD_INR": {
                "direct": ["TCS.NS", "INFY.NS"],  # Weak rupee helps IT exporters
                "inverse": ["MARUTI.NS"],  # Hurts importers
            },
            "US_10Y_YIELD": {
                "inverse": ["NIFTY_MIDCAP.NS"]  # High cost of capital hurts growth/midcaps
            },
        }
        logger.info("CausalityEngine initialized.")

    def run_causality_check(self, macro_data: Dict[str, float]) -> List[str]:
        """
        Checks current macro regime and issues strategic warnings or boosts.
        macro_data expectations: "crude_oil_change_pct", "usd_inr_change_pct", etc.
        """
        insights = []

        crude = macro_data.get("crude_oil_change_pct", 0.0)
        if crude > 0.03:
            insights.append(
                f"Global Risk: Crude spiked {crude:.1%}. Bearish pressure expected on Aviation/Paints "  # noqa: E501
                f"({', '.join(self._rules['CRUDE_OIL']['inverse'])})."
            )
        elif crude < -0.03:
            insights.append(
                f"Global Tailwinds: Crude dropped {crude:.1%}. Bullish setup for Aviation/Paints."
            )

        usd_inr = macro_data.get("usd_inr_change_pct", 0.0)
        if usd_inr > 0.02:
            insights.append(
                f"Currency Shift: INR weakening ({usd_inr:.1%}). Direct benefit to IT Exporters "
                f"({', '.join(self._rules['USD_INR']['direct'])})."
            )

        # In a real model, we would compute exact sentiment offsets for these tickers here.
        return insights
