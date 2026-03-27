"""
Healer Engine (Portfolio Recovery)
===================================
Identifies permanently damaged stocks (-15% down + negative sentiment)
and triggers "Tax-Loss Harvesting". Reallocates that capital into
identified High-Momentum stocks.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict

logger = logging.getLogger(__name__)


@dataclass
class Position:
    ticker: str
    entry_price: float
    current_price: float
    sentiment_score: float
    momentum_score: float


@dataclass
class HealerAction:
    ticker_to_sell: str
    ticker_to_buy: str
    reasoning: str


class HealerEngine:
    """The 'Healer' identifying rotation opportunities for damaged capital."""

    def __init__(self, panic_threshold: float = -0.15, sentiment_threshold: float = -0.3):
        self.panic_threshold = panic_threshold
        self.sentiment_threshold = sentiment_threshold
        logger.info("HealerEngine initialized.")

    def evaluate_portfolio(
        self, positions: List[Position], candidates: List[Position]
    ) -> List[HealerAction]:
        """
        Scans current positions for weak links and finds high-momentum
        candidates for capital rotation.
        """
        actions = []
        weak_links = []

        # 1. Identify weak links
        for pos in positions:
            pnl_pct = (pos.current_price - pos.entry_price) / pos.entry_price
            if pnl_pct <= self.panic_threshold and pos.sentiment_score <= self.sentiment_threshold:
                weak_links.append(pos)
                logger.warning(
                    f"Weak Link Identified: {pos.ticker} (PnL: {pnl_pct:.1%}, Sentiment: {pos.sentiment_score})"  # noqa: E501
                )

        if not weak_links:
            return actions

        # 2. Find High-Momentum replacements
        strong_candidates = [
            c for c in candidates if c.momentum_score > 0.7 and c.sentiment_score > 0.5
        ]

        # Sort candidates by momentum (highest first)
        strong_candidates.sort(key=lambda x: x.momentum_score, reverse=True)

        # 3. Pair sells with buys
        for weak in weak_links:
            if strong_candidates:
                replacement = strong_candidates.pop(0)
                reason = (
                    f"Tax-Loss Harvesting {weak.ticker} (-{abs((weak.current_price-weak.entry_price)/weak.entry_price):.1%} loss, "  # noqa: E501
                    f"sentiment {weak.sentiment_score}). Rotating capital to strong momentum {replacement.ticker} "  # noqa: E501
                    f"(momentum {replacement.momentum_score})."
                )
                actions.append(HealerAction(weak.ticker, replacement.ticker, reason))
            else:
                # No strong candidates; sell to cash
                actions.append(
                    HealerAction(
                        weak.ticker, "CASH", f"Liquidating {weak.ticker} to preserve capital."
                    )
                )

        return actions
