import logging
from datetime import datetime
import zoneinfo

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class SentimentAnalyst:
    """
    Analyzes Indian domestic newsflow, regulatory dispatches, and corporate disclosures.
    Zero-latency heuristic parsing specialized for SEBI regulatory signals, CBI/ED probes, and institutional flows.
    """

    BULLISH_KEYWORDS = [
        "strong", "beat", "upgrade", "buy", "rally", "surge", "record",
        "profit", "order win", "dividend", "capex", "inflow", "turnaround",
        "qip", "buyback", "expansion", "growth", "all-time high"
    ]

    BEARISH_KEYWORDS = [
        "weak", "miss", "downgrade", "sell", "crash", "loss", "fraud",
        "probe", "notice", "default", "penalty", "slump", "outflow",
        "insolvency", "nclt", "debt recast", "resignation", "investigation"
    ]

    REGULATORY_RED_FLAGS = ["sebi notice", "ed raid", "cbi probe", "tax evasion", "forensic audit", "insider trading"]

    async def analyze(self, ticker: str, headlines: list[str]) -> dict:
        current_time = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        total_headlines = len(headlines)

        if not headlines:
            return {
                "analyst": "SentimentAnalyst",
                "ticker": ticker,
                "overall_sentiment": "NEUTRAL",
                "sentiment_score": 0.0,
                "sebi_risk_flag": False,
                "fii_signal": "NEUTRAL",
                "headline_count": 0,
                "summary": f"[{ticker}] No fresh Indian media dispatches detected. Defaulting to neutral posture.",
                "analyzed_at": current_time,
            }

        bull_count = 0
        bear_count = 0
        sebi_risk_detected = False
        fii_buy_detected = False
        fii_sell_detected = False

        for hl in headlines:
            text = hl.lower()

            for kw in self.BULLISH_KEYWORDS:
                if kw in text:
                    bull_count += 1
            for kw in self.BEARISH_KEYWORDS:
                if kw in text:
                    bear_count += 1
            for rf in self.REGULATORY_RED_FLAGS:
                if rf in text:
                    sebi_risk_detected = True
                    bear_count += 3

            if "fii buy" in text or "fii inflow" in text or "dii accumulation" in text:
                fii_buy_detected = True
            if "fii sell" in text or "fii outflow" in text:
                fii_sell_detected = True

        net_raw = bull_count - bear_count
        divisor = max(1, bull_count + bear_count)
        sentiment_score = round(max(-1.0, min(1.0, net_raw / divisor)), 3)

        if sebi_risk_detected:
            sentiment_score = min(-0.6, sentiment_score)
            overall_sentiment = "REGULATORY_ALERT_BEARISH"
        elif sentiment_score > 0.25:
            overall_sentiment = "BULLISH"
        elif sentiment_score < -0.25:
            overall_sentiment = "BEARISH"
        else:
            overall_sentiment = "NEUTRAL"

        if fii_buy_detected and not fii_sell_detected:
            fii_signal = "BUYING"
        elif fii_sell_detected and not fii_buy_detected:
            fii_signal = "SELLING"
        else:
            fii_signal = "NEUTRAL"

        summary = (
            f"[{ticker}] Sentiment: {overall_sentiment} (Score: {sentiment_score:+0.2f}, "
            f"Headlines: {total_headlines}, SEBI Flag: {sebi_risk_detected}, FII Mood: {fii_signal})."
        )

        logger.info(f"[ANALYST COUNCIL - SENTIMENT] {summary}")

        return {
            "analyst": "SentimentAnalyst",
            "ticker": ticker,
            "overall_sentiment": overall_sentiment,
            "sentiment_score": sentiment_score,
            "sebi_risk_flag": sebi_risk_detected,
            "fii_signal": fii_signal,
            "headline_count": total_headlines,
            "summary": summary,
            "analyzed_at": current_time,
        }
