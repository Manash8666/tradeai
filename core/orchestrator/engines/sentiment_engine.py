"""
Sentiment Engine (The News Engine)
===================================
A proxy for FinBERT/NLP sentiment analysis. In this implementation, it
leverages the `ai_agent.llm_client.get_liquid_client()` (LFM-2.5) to quickly
score global and local news headlines into a normalized SentimentScore.
"""

import logging
from dataclasses import dataclass
from typing import List

from ai_agent.llm_client import get_liquid_client, LLMMessage

logger = logging.getLogger(__name__)


@dataclass
class SentimentScore:
    asset: str
    score: float  # -1.0 (Extremely Bearish) to 1.0 (Extremely Bullish)
    label: str  # "Bullish", "Neutral", "Bearish"
    reasoning: str


class SentimentEngine:
    """Evaluates the collective mood using LLM-based NLP scoring."""

    def __init__(self):
        self._llm = get_liquid_client()
        logger.info("SentimentEngine initialized.")

    async def analyze_headlines(self, asset: str, headlines: List[str]) -> SentimentScore:
        """
        Passes recent headlines to the fast thinking model to extract a
        financial sentiment score.
        """
        if not headlines:
            return SentimentScore(asset, 0.0, "Neutral", "No news available.")

        prompt = (
            f"Analyze these recent headlines for '{asset}':\n"
            + "\n".join(f"- {h}" for h in headlines)
            + "\n\nAssign a sentiment score between -1.0 (Bearish) and 1.0 (Bullish). "
            "Reply strictly in this format: Score | Label | Brief Reason."
            "\nExample: 0.8 | Bullish | Strong earnings growth."
        )

        try:
            resp = await self._llm.ask([LLMMessage(role="user", content=prompt)])
            # Basic parsing of the structured response
            parts = resp.content.split("|")
            score = float(parts[0].strip())
            label = parts[1].strip()
            reasoning = parts[2].strip() if len(parts) > 2 else ""

            # Clamp score
            score = max(-1.0, min(1.0, score))

            logger.debug(f"[{asset}] Sentiment: {score} ({label})")
            return SentimentScore(asset, score, label, reasoning)

        except Exception as exc:
            logger.warning(f"Sentiment analysis failed for {asset}: {exc}")
            return SentimentScore(asset, 0.0, "Neutral", "Analysis failed.")
