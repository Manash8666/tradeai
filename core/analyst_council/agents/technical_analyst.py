import logging
from datetime import datetime
import zoneinfo

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class TechnicalAnalyst:
    """
    Evaluates price action, momentum, range positioning, and volume dynamics
    for NSE/BSE securities using pure math without heavy external dependencies.
    """

    async def analyze(self, ticker: str, market_data: dict) -> dict:
        current_time = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

        current_price = float(market_data.get("current_price", 100.0))
        high_price = float(market_data.get("high", current_price))
        low_price = float(market_data.get("low", current_price))
        prev_close = float(market_data.get("prev_close", current_price))
        volume = float(market_data.get("volume", 100000.0))
        avg_volume_20d = float(market_data.get("avg_volume_20d", 100000.0))
        week_52_high = float(market_data.get("week_52_high", current_price * 1.2))
        week_52_low = float(market_data.get("week_52_low", current_price * 0.8))

        vwap_proxy = (high_price + low_price + current_price) / 3.0
        vwap_signal = "ABOVE" if current_price >= vwap_proxy else "BELOW"
        volume_surge = round(volume / max(1.0, avg_volume_20d), 2)

        range_span = max(1e-5, week_52_high - week_52_low)
        position_in_range = round(max(0.0, min(1.0, (current_price - week_52_low) / range_span)), 3)

        pct_change = (current_price - prev_close) / max(1e-5, prev_close)
        if pct_change >= 0.005:
            trend = "UPTREND"
            trend_score = 0.5
        elif pct_change <= -0.005:
            trend = "DOWNTREND"
            trend_score = -0.5
        else:
            trend = "SIDEWAYS"
            trend_score = 0.0

        intraday_span = max(1e-5, high_price - low_price)
        intraday_relative = (current_price - low_price) / intraday_span
        rsi_proxy = round((intraday_relative * 0.5 + position_in_range * 0.5) * 100, 1)

        vwap_score = 0.25 if vwap_signal == "ABOVE" else -0.25
        vol_score = 0.25 if volume_surge >= 1.25 and trend == "UPTREND" else (-0.25 if volume_surge >= 1.25 and trend == "DOWNTREND" else 0.0)
        range_score = (position_in_range - 0.5) * 0.5

        technical_score = round(max(-1.0, min(1.0, trend_score + vwap_score + vol_score + range_score)), 3)

        summary = (
            f"[{ticker}] Technicals: {trend} (Price: ₹{current_price:,.2f}, Chg: {pct_change*100:+.2f}%). "
            f"VWAP: {vwap_signal} (₹{vwap_proxy:,.2f}), Vol Surge: {volume_surge}x, "
            f"52W Range: {position_in_range*100:.1f}%, Score: {technical_score:+0.2f}."
        )

        logger.info(f"[ANALYST COUNCIL - TECHNICAL] {summary}")

        return {
            "analyst": "TechnicalAnalyst",
            "ticker": ticker,
            "trend": trend,
            "rsi_proxy": rsi_proxy,
            "vwap_signal": vwap_signal,
            "vwap_value": round(vwap_proxy, 2),
            "volume_surge": volume_surge,
            "position_in_range": position_in_range,
            "technical_score": technical_score,
            "summary": summary,
            "analyzed_at": current_time,
        }
