import logging
from dataclasses import dataclass
from typing import Dict, Any
import numpy as np

from .indian_ta_library import IndianTALibrary

logger = logging.getLogger(__name__)


@dataclass
class MultiTimeframeSignal:
    ticker: str
    trend_alignment: int  # 0 to 4 (how many timeframes agree)
    overall_signal: str  # "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL"
    confidence: float  # 0.0 to 1.0
    higher_timeframe_bias: str  # "BULLISH" | "BEARISH" | "NEUTRAL"
    per_timeframe: Dict[str, Any]
    rationale: str


class MultiTimeframeEngine:
    """
    Synchronizes Technical Indicators across multiple temporal fractal horizons (5m, 15m, 1h, 1D).
    Enforces the 'Higher Timeframe Dominance' rule: intraday 5m noisy buy signals
    are suppressed if daily and hourly institutional trends are trending downwards.
    """

    TIMEFRAMES = ["5m", "15m", "1h", "1D"]

    def __init__(self):
        logger.info("[MTF ENGINE] Multi-Timeframe Alignment Processor online.")

    def sync_signals(self, ticker: str, candle_data: Dict[str, Dict[str, np.ndarray]]) -> MultiTimeframeSignal:
        """
        Processes multi-timeframe OHLCV datasets and evaluates alignment.
        candle_data format: { "5m": {"high": ..., "low": ..., "close": ...}, "15m": ... }
        """
        results_per_tf = {}
        bullish_count = 0
        bearish_count = 0

        for tf in self.TIMEFRAMES:
            data = candle_data.get(tf)
            if not data or len(data.get("close", [])) < 20:
                results_per_tf[tf] = {"status": "INSUFFICIENT_DATA", "bias": "NEUTRAL"}
                continue

            closes = np.asarray(data["close"], dtype=float)
            highs = np.asarray(data["high"], dtype=float)
            lows = np.asarray(data["low"], dtype=float)

            rsi_series = IndianTALibrary.rsi(closes, 14)
            latest_rsi = float(rsi_series[-1]) if len(rsi_series) > 0 else 50.0

            ema_20 = IndianTALibrary.ema(closes, 20)
            latest_ema = float(ema_20[-1]) if len(ema_20) > 0 else closes[-1]
            price_above_ema = closes[-1] >= latest_ema

            _, direction = IndianTALibrary.supertrend(highs, lows, closes, 7, 3.0)
            st_bullish = direction[-1] == 1

            if st_bullish and price_above_ema and latest_rsi > 48.0:
                bias = "BULLISH"
                bullish_count += 1
            elif not st_bullish and not price_above_ema and latest_rsi < 52.0:
                bias = "BEARISH"
                bearish_count += 1
            else:
                bias = "NEUTRAL"

            results_per_tf[tf] = {
                "bias": bias,
                "rsi": round(latest_rsi, 1),
                "close": round(float(closes[-1]), 2),
                "supertrend_bullish": st_bullish,
                "above_ema20": price_above_ema,
            }

        # Higher Timeframe (1D) Dominance Rule
        daily_bias = results_per_tf.get("1D", {}).get("bias", "NEUTRAL")

        if daily_bias == "BEARISH":
            # Suppress intraday false buy signals
            if results_per_tf.get("5m", {}).get("bias") == "BULLISH":
                results_per_tf["5m"]["suppressed"] = True
                bullish_count = max(0, bullish_count - 1)

        trend_alignment = max(bullish_count, bearish_count)
        confidence = round(trend_alignment / 4.0, 2)

        if bullish_count == 4:
            overall_signal = "STRONG_BUY"
            rationale = "Full 4-horizon bullish fractal alignment across 5m, 15m, 1h, and Daily."
        elif bullish_count >= 3:
            overall_signal = "BUY"
            rationale = "Dominant bullish alignment supported by higher timeframe direction."
        elif bearish_count == 4:
            overall_signal = "STRONG_SELL"
            rationale = "Full 4-horizon bearish breakdown across all time horizons."
        elif bearish_count >= 3:
            overall_signal = "SELL"
            rationale = "Sustained institutional selling pressure across multiple timeframes."
        else:
            overall_signal = "NEUTRAL"
            rationale = "Conflicting signals between intraday noise and higher timeframe trends."

        return MultiTimeframeSignal(
            ticker=ticker,
            trend_alignment=trend_alignment,
            overall_signal=overall_signal,
            confidence=confidence,
            higher_timeframe_bias=daily_bias,
            per_timeframe=results_per_tf,
            rationale=rationale,
        )
