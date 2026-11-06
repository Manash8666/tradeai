import logging
from datetime import datetime
import zoneinfo

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class BearResearcher:
    """
    Stress-tests prospective trades by formulating adversarial bear cases,
    identifying promoter pledging hazards, SEBI regulatory scrutiny, and liquidity drawdowns.
    """

    async def build_case(self, ticker: str, analyst_reports: dict) -> dict:
        current_time = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

        fund = analyst_reports.get("fundamentals", {})
        sent = analyst_reports.get("sentiment", {})
        tech = analyst_reports.get("technicals", {})
        fii = analyst_reports.get("fii_dii", {})

        risks = []
        risk_weight = 0.0

        # Regulatory checks
        if sent.get("sebi_risk_flag", False):
            risks.append("CRITICAL: Active regulatory notice / SEBI / investigation headlines detected.")
            risk_weight += 0.45

        # Valuation & Debt checks
        if fund.get("debt_risk") == "HIGH":
            risks.append(f"Elevated solvency concern: High Debt-to-Equity or promoter pledge ({fund.get('promoter_pledge_pct', 0)}%).")
            risk_weight += 0.25

        if fund.get("pe_signal") == "EXPENSIVE":
            risks.append("Valuation overstretch vs benchmark Nifty multiples.")
            risk_weight += 0.15

        # Technical breakdown checks
        if tech.get("trend") == "DOWNTREND":
            risks.append("Sustained lower-highs and trading below intraday VWAP benchmark.")
            risk_weight += 0.20

        # Institutional outflows
        if fii.get("net_institutional_flow") == "BEARISH":
            risks.append(f"Institutional distribution underway: Combined outflow of ₹{abs(fii.get('net_flow_cr', 0)):,.0f} Cr.")
            risk_weight += 0.25

        # If clean, add systemic Indian risk (INR depreciation / Crude oil shock)
        if not risks:
            risks.append("Systemic Indian macro sensitivity: Elevated Brent crude prices & INR/USD currency volatility risk.")
            risk_weight += 0.15

        bear_score = round(min(1.0, risk_weight), 2)
        max_downside_pct = round(max(1.8, bear_score * 7.0), 1)
        stop_loss_suggestion_pct = round(max(1.0, max_downside_pct * 0.45), 1)

        bear_thesis = (
            f"Bear Case for {ticker}: Flagging {len(risks)} distinct risk factors. "
            f"{' '.join(risks[:2])} "
            f"Estimated max adverse excursion -{max_downside_pct}%. Stop-loss recommended at -{stop_loss_suggestion_pct}%."
        )

        logger.info(f"[ANALYST COUNCIL - BEAR RESEARCHER] {bear_thesis}")

        return {
            "researcher": "BearResearcher",
            "ticker": ticker,
            "bear_thesis": bear_thesis,
            "bear_score": bear_score,
            "key_risks": risks,
            "max_downside_pct": max_downside_pct,
            "stop_loss_suggestion_pct": stop_loss_suggestion_pct,
            "generated_at": current_time,
        }
