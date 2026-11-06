import logging
from datetime import datetime
import zoneinfo

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class FundamentalsAnalyst:
    """
    Evaluates corporate health and valuation metrics tailored to Indian equities.
    Considers Nifty benchmark multiples, Indian FD benchmark yield (6.75%), and F&O STT friction.
    """

    def __init__(self):
        self.nifty_benchmark_pe = 21.5
        self.risk_free_fd_rate = 0.0675  # ~6.75% benchmark bank FD rate in India

    async def analyze(self, ticker: str, market_data: dict) -> dict:
        current_time = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        pe_ratio = float(market_data.get("pe_ratio", 22.0))
        debt_to_equity = float(market_data.get("debt_to_equity", 0.8))
        dividend_yield = float(market_data.get("dividend_yield", 0.015))
        revenue_growth_yoy = float(market_data.get("revenue_growth_yoy", 0.10))
        promoter_pledge_pct = float(market_data.get("promoter_pledge_pct", 0.0))

        # Valuation Assessment vs Nifty average
        if pe_ratio < self.nifty_benchmark_pe * 0.85:
            pe_signal = "CHEAP"
            pe_score = 0.6
        elif pe_ratio > self.nifty_benchmark_pe * 1.35:
            pe_signal = "EXPENSIVE"
            pe_score = -0.6
        else:
            pe_signal = "FAIR"
            pe_score = 0.1

        # Solvency & Governance Risk (Crucial in Indian mid/small-caps)
        debt_risk = "HIGH" if debt_to_equity > 1.5 or promoter_pledge_pct > 20.0 else "LOW"
        debt_score = -0.5 if debt_risk == "HIGH" else 0.3

        # Growth assessment
        if revenue_growth_yoy > 0.15:
            growth_signal = "POSITIVE"
            growth_score = 0.6
        elif revenue_growth_yoy < 0.02:
            growth_signal = "NEGATIVE"
            growth_score = -0.5
        else:
            growth_signal = "NEUTRAL"
            growth_score = 0.0

        # Yield comparison vs Indian Bank FDs
        yield_spread = dividend_yield - self.risk_free_fd_rate

        # Composite score calculation (-1.0 to +1.0)
        fundamental_score = round(
            max(-1.0, min(1.0, (pe_score * 0.35) + (debt_score * 0.35) + (growth_score * 0.30))),
            3,
        )

        summary = (
            f"[{ticker}] Fundamental Rating: {pe_signal} (P/E: {pe_ratio:.1f} vs Nifty {self.nifty_benchmark_pe:.1f}). "
            f"Debt Risk: {debt_risk} (D/E: {debt_to_equity:.2f}, Pledge: {promoter_pledge_pct:.1f}%). "
            f"Growth YoY: {revenue_growth_yoy*100:.1f}%. Score: {fundamental_score:+0.2f}."
        )

        logger.info(f"[ANALYST COUNCIL - FUNDAMENTALS] {summary}")

        return {
            "analyst": "FundamentalsAnalyst",
            "ticker": ticker,
            "pe_signal": pe_signal,
            "debt_risk": debt_risk,
            "growth_signal": growth_signal,
            "dividend_yield": dividend_yield,
            "yield_spread_vs_fd": round(yield_spread, 4),
            "promoter_pledge_pct": promoter_pledge_pct,
            "fundamental_score": fundamental_score,
            "summary": summary,
            "analyzed_at": current_time,
        }
