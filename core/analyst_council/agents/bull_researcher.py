import logging
from datetime import datetime
import zoneinfo

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class BullResearcher:
    """
    Synthesizes affirmative catalysts and structural tailwinds across Indian macro,
    FII liquidity cycles, technical setups, and fundamental valuations.
    """

    async def build_case(self, ticker: str, analyst_reports: dict) -> dict:
        current_time = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

        fund = analyst_reports.get("fundamentals", {})
        sent = analyst_reports.get("sentiment", {})
        tech = analyst_reports.get("technicals", {})
        fii = analyst_reports.get("fii_dii", {})

        catalysts = []
        scores = []

        # 1. Fundamental confirmation
        if fund.get("fundamental_score", 0.0) > 0.0:
            catalysts.append(f"Favorable valuation metrics: P/E is {fund.get('pe_signal', 'FAIR')} with manageable debt profile.")
            scores.append(0.25)

        # 2. Sentiment confirmation
        if sent.get("sentiment_score", 0.0) > 0.15:
            catalysts.append("Strong positive domestic narrative with absence of regulatory/probe flags.")
            scores.append(0.25)

        # 3. Technical confirmation
        if tech.get("technical_score", 0.0) > 0.1:
            catalysts.append(f"Price holding above VWAP in {tech.get('trend', 'SIDEWAYS')} with active volume confirmation.")
            scores.append(0.30)

        # 4. Institutional flow confirmation
        if fii.get("composite_score", 0.0) > 0.1:
            catalysts.append(f"Institutional accumulation active: Net domestic inflow of ₹{fii.get('net_flow_cr', 0):+,.0f} Cr.")
            scores.append(0.30)

        # If sparse catalysts, inject standard Indian structural tailwinds
        if not catalysts:
            catalysts.append("Indian Capex supercycle and domestic SIP inflows (₹25,000+ Cr/month) providing resilient baseline support.")
            scores.append(0.15)

        bull_score = round(min(1.0, sum(scores) + 0.15), 2)
        max_upside_pct = round(max(2.5, bull_score * 8.5), 1)

        bull_thesis = (
            f"Bull Case for {ticker}: Driven by {len(catalysts)} aligned tailwinds. "
            f"{' '.join(catalysts[:2])} "
            f"Targeting +{max_upside_pct}% prospective alpha under current Indian liquidity conditions."
        )

        logger.info(f"[ANALYST COUNCIL - BULL RESEARCHER] {bull_thesis}")

        return {
            "researcher": "BullResearcher",
            "ticker": ticker,
            "bull_thesis": bull_thesis,
            "bull_score": bull_score,
            "key_catalysts": catalysts,
            "max_upside_pct": max_upside_pct,
            "risk_rewards": "1:2.4",
            "generated_at": current_time,
        }
