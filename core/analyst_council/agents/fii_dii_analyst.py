import logging
from datetime import datetime
import zoneinfo

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class FIIDIIAnalyst:
    """
    Dedicated Institutional Flow Analyst for the Indian Market.
    Decodes Foreign Institutional Investor (FII) & Domestic Institutional Investor (DII)
    cash/derivatives positioning, GIFT Nifty arbitrage signals, and Index Futures net contracts.
    """

    async def analyze(self, ticker: str, market_data: dict) -> dict:
        current_time = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

        # Inflow/Outflow metrics in Crores (₹ Cr)
        fii_net_inflow_cr = float(market_data.get("fii_net_inflow_cr", 250.0))
        dii_net_inflow_cr = float(market_data.get("dii_net_inflow_cr", 650.0))
        fii_index_futures_net = int(market_data.get("fii_index_futures_net", 12000))  # Contracts net long/short
        fii_pcr = float(market_data.get("fii_pcr", 0.95))
        gift_nifty_premium = float(market_data.get("gift_nifty_premium", 25.0))  # Points

        # FII strength (-1.0 to 1.0)
        if fii_net_inflow_cr > 1000.0:
            fii_strength = 0.85
        elif fii_net_inflow_cr > 200.0:
            fii_strength = 0.45
        elif fii_net_inflow_cr < -1000.0:
            fii_strength = -0.85
        elif fii_net_inflow_cr < -200.0:
            fii_strength = -0.45
        else:
            fii_strength = 0.0

        # DII strength (-1.0 to 1.0)
        dii_strength = round(max(-1.0, min(1.0, dii_net_inflow_cr / 1500.0)), 2)

        # Net Domestic Institutional Flow
        net_flow_cr = fii_net_inflow_cr + dii_net_inflow_cr
        if net_flow_cr > 500.0:
            net_institutional_flow = "BULLISH"
        elif net_flow_cr < -500.0:
            net_institutional_flow = "BEARISH"
        else:
            net_institutional_flow = "MIXED"

        # Structural Bias considering FII Index Futures & GIFT spread
        futures_bullish = fii_index_futures_net > 5000
        gift_bullish = gift_nifty_premium > 15.0

        if net_institutional_flow == "BULLISH" and futures_bullish:
            institutional_bias = "ACCUMULATION"
            composite_score = 0.75
        elif net_institutional_flow == "BEARISH" and not futures_bullish:
            institutional_bias = "DISTRIBUTION"
            composite_score = -0.75
        else:
            institutional_bias = "NEUTRAL"
            composite_score = 0.10 if gift_bullish else -0.10

        summary = (
            f"[{ticker}] Institutional Flows: {institutional_bias} (FII: ₹{fii_net_inflow_cr:+,.0f} Cr, "
            f"DII: ₹{dii_net_inflow_cr:+,.0f} Cr, Net: ₹{net_flow_cr:+,.0f} Cr). "
            f"FII Futures Net: {fii_index_futures_net:,} lots, GIFT Premium: {gift_nifty_premium:+0.1f} pts."
        )

        logger.info(f"[ANALYST COUNCIL - FII/DII] {summary}")

        return {
            "analyst": "FIIDIIAnalyst",
            "ticker": ticker,
            "institutional_bias": institutional_bias,
            "net_institutional_flow": net_institutional_flow,
            "fii_net_inflow_cr": fii_net_inflow_cr,
            "dii_net_inflow_cr": dii_net_inflow_cr,
            "net_flow_cr": net_flow_cr,
            "fii_strength": fii_strength,
            "dii_strength": dii_strength,
            "fii_index_futures_net": fii_index_futures_net,
            "gift_nifty_premium": gift_nifty_premium,
            "composite_score": composite_score,
            "summary": summary,
            "analyzed_at": current_time,
        }
