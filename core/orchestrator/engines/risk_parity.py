"""
Risk-Parity Analysis (Minimum Loss)
====================================
Dynamically allocates capital between High-Risk (Equity), 
Medium-Risk (Debt), and Safe-Haven (Gold) based on real-time 
volatility (India VIX).
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AllocationWeights:
    equity_pct: float
    debt_pct: float
    gold_pct: float
    reason: str


class RiskParityEngine:
    """Manages cross-asset capital allocation to blunt market crashes."""

    def __init__(self, normal_vix_range: tuple = (12.0, 18.0)):
        self.normal_vix_range = normal_vix_range
        logger.info("RiskParityEngine initialized.")

    def compute_optimal_allocation(self, current_vix: float) -> AllocationWeights:
        """
        Shifts away from equity into gold/debt as volatility spikes.
        Follows a simplified inverse-volatility parity model.
        """
        min_vix, max_vix = self.normal_vix_range

        if current_vix < min_vix:
            # "Greed" / Complacency mode — max equity.
            return AllocationWeights(
                equity_pct=0.80,
                debt_pct=0.15,
                gold_pct=0.05,
                reason=f"VIX ({current_vix:.1f}) below normal range. Heavily weighted to Equity.",
            )

        elif current_vix > 25.0:
            # "Panic" / Crash mode — capital flight to safety.
            return AllocationWeights(
                equity_pct=0.30,
                debt_pct=0.40,
                gold_pct=0.30,
                reason=f"VIX ({current_vix:.1f}) in panic zone (>25). Drastically reduced Equity, heavily boosted Gold/Debt.",  # noqa: E501
            )

        elif current_vix > max_vix:
            # Elevated risk
            return AllocationWeights(
                equity_pct=0.50,
                debt_pct=0.30,
                gold_pct=0.20,
                reason=f"VIX ({current_vix:.1f}) is elevated. Balancing portfolios.",
            )

        else:
            # Normal range
            return AllocationWeights(
                equity_pct=0.65,
                debt_pct=0.25,
                gold_pct=0.10,
                reason=f"VIX ({current_vix:.1f}) in normal bounds. Standard 65/25/10 allocation.",
            )
