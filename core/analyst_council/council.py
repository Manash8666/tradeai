import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List
import zoneinfo

from .agents.fundamentals_analyst import FundamentalsAnalyst
from .agents.sentiment_analyst import SentimentAnalyst
from .agents.technical_analyst import TechnicalAnalyst
from .agents.fii_dii_analyst import FIIDIIAnalyst
from .agents.bull_researcher import BullResearcher
from .agents.bear_researcher import BearResearcher

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


@dataclass
class CouncilVerdict:
    ticker: str
    direction: str  # "BUY" | "SELL" | "HOLD"
    confidence: float  # 0.0 to 1.0
    bull_thesis: str
    bear_thesis: str
    final_rationale: str
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH"
    suggested_position_size_pct: float
    ist_timestamp: str
    analyst_breakdown: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IndianAnalystCouncil:
    """
    Hierarchical Multi-Agent Quant Council for the Indian Markets.
    Coordinates 4 domain specialists and an adversarial Bull/Bear committee
    to produce institutional consensus trade decisions with explainability trails.
    """

    def __init__(self):
        self.fundamentals = FundamentalsAnalyst()
        self.sentiment = SentimentAnalyst()
        self.technicals = TechnicalAnalyst()
        self.fii_dii = FIIDIIAnalyst()
        self.bull_researcher = BullResearcher()
        self.bear_researcher = BearResearcher()
        logger.info("[ANALYST COUNCIL] Initialized 6-agent deliberative architecture for NSE/BSE.")

    async def run_council_session(
        self,
        ticker: str,
        market_data: dict,
        headlines: List[str] | None = None,
    ) -> CouncilVerdict:
        """
        Executes a 2-stage deliberative council session:
        Stage 1: Concurrent analysis across Fundamentals, Sentiment, Technicals, and FII/DII flows.
        Stage 2: Adversarial synthesis through Bull and Bear researchers.
        Stage 3: Adjudication and final verdict computation.
        """
        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        headlines = headlines or []

        try:
            logger.info(f"[ANALYST COUNCIL] Starting deliberation for {ticker}...")

            # Stage 1: Parallel Analyst Dispatches
            fund_res, sent_res, tech_res, fii_res = await asyncio.gather(
                self.fundamentals.analyze(ticker, market_data),
                self.sentiment.analyze(ticker, headlines),
                self.technicals.analyze(ticker, market_data),
                self.fii_dii.analyze(ticker, market_data),
            )

            analyst_reports = {
                "fundamentals": fund_res,
                "sentiment": sent_res,
                "technicals": tech_res,
                "fii_dii": fii_res,
            }

            # Stage 2: Adversarial Bull vs Bear Debate
            bull_case, bear_case = await asyncio.gather(
                self.bull_researcher.build_case(ticker, analyst_reports),
                self.bear_researcher.build_case(ticker, analyst_reports),
            )

            # Stage 3: Council Adjudication
            bull_score = bull_case.get("bull_score", 0.5)
            bear_score = bear_case.get("bear_score", 0.5)
            net_delta = bull_score - bear_score

            # Regulatory override rule: If regulatory red flag, automatically HOLD or SELL
            sebi_alert = sent_res.get("sebi_risk_flag", False)

            if sebi_alert:
                direction = "SELL" if tech_res.get("trend") == "DOWNTREND" else "HOLD"
                confidence = 0.85
                risk_level = "HIGH"
                pos_size = 0.0
                final_rationale = "SEBI / Regulatory investigation red flag detected. Risk department enforces capital preservation."
            elif net_delta >= 0.20:
                direction = "BUY"
                confidence = round(min(0.95, 0.55 + net_delta * 0.4), 2)
                risk_level = "LOW" if bear_score < 0.35 else "MEDIUM"
                pos_size = round(max(2.0, min(10.0, confidence * 10.0)), 1)
                final_rationale = (
                    f"Council consensus affirmative (Bull +{bull_score:.2f} vs Bear -{bear_score:.2f}). "
                    f"Aligned institutional flow and technical momentum support entry."
                )
            elif net_delta <= -0.20:
                direction = "SELL"
                confidence = round(min(0.95, 0.55 + abs(net_delta) * 0.4), 2)
                risk_level = "HIGH" if bear_score > 0.65 else "MEDIUM"
                pos_size = round(max(2.0, min(8.0, confidence * 8.0)), 1)
                final_rationale = (
                    f"Council consensus defensive (Bear -{bear_score:.2f} dominates Bull +{bull_score:.2f}). "
                    f"Technical breakdown and institutional distribution warrant exit/short."
                )
            else:
                direction = "HOLD"
                confidence = 0.50
                risk_level = "MEDIUM"
                pos_size = 0.0
                final_rationale = (
                    f"Council split deliberation (Bull {bull_score:.2f} vs Bear {bear_score:.2f}). "
                    f"Risk-reward equilibrium does not offer clear statistical alpha."
                )

            verdict = CouncilVerdict(
                ticker=ticker,
                direction=direction,
                confidence=confidence,
                bull_thesis=bull_case.get("bull_thesis", ""),
                bear_thesis=bear_case.get("bear_thesis", ""),
                final_rationale=final_rationale,
                risk_level=risk_level,
                suggested_position_size_pct=pos_size,
                ist_timestamp=now_str,
                analyst_breakdown={
                    **analyst_reports,
                    "bull_case": bull_case,
                    "bear_case": bear_case,
                },
            )

            logger.info(
                f"[ANALYST COUNCIL] Verdict for {ticker}: {verdict.direction} "
                f"(Conf: {verdict.confidence*100:.0f}%, Risk: {verdict.risk_level})"
            )
            return verdict

        except Exception as exc:
            logger.error(f"[ANALYST COUNCIL] Error during council deliberation: {exc}", exc_info=True)
            return CouncilVerdict(
                ticker=ticker,
                direction="HOLD",
                confidence=0.0,
                bull_thesis="Session interrupted.",
                bear_thesis="Execution safety fallback engaged.",
                final_rationale=f"Deliberation aborted due to unexpected exception: {exc}",
                risk_level="HIGH",
                suggested_position_size_pct=0.0,
                ist_timestamp=now_str,
                analyst_breakdown={},
            )
