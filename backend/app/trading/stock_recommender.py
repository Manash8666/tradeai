"""
Multi-Horizon Stock & Index Prediction Engine.
Inspired by woshijielie/stock_prediction_and_recommendation.

Computes technical feature vectors (EMA crossovers, RSI-14, MACD, Bollinger %B, Volume Thrust)
and provides multi-horizon probabilistic forecasts (15m scalp, 1h intraday, End of Day)
with defined target and stop-loss levels in ₹ INR.
"""

import math
from typing import List, Dict, Any, Optional
import numpy as np


class StockRecommender:
    """
    Multi-horizon quantitative signal predictor and trade setup recommender.
    """

    @staticmethod
    def extract_technical_features(candles: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculates normalized technical indicator features on close prices."""
        if len(candles) < 20:
            return {
                "rsi_14": 50.0,
                "ema_spread_pct": 0.0,
                "macd_hist": 0.0,
                "bollinger_pct_b": 0.5,
                "atr_pct": 0.8,
            }

        closes = np.array([c["close"] for c in candles], dtype=np.float64)
        highs = np.array([c["high"] for c in candles], dtype=np.float64)
        lows = np.array([c["low"] for c in candles], dtype=np.float64)

        # 1. RSI 14
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 1.0
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 1.0
        rs = avg_gain / max(1e-6, avg_loss)
        rsi = 100.0 - (100.0 / (1.0 + rs))

        # 2. EMA Spread (EMA 9 vs EMA 21)
        ema_9 = float(np.mean(closes[-9:]))
        ema_21 = float(np.mean(closes[-21:]))
        ema_spread = ((ema_9 - ema_21) / ema_21) * 100.0

        # 3. MACD Histogram Proxy
        ema_12 = float(np.mean(closes[-12:]))
        ema_26 = float(np.mean(closes[-26:])) if len(closes) >= 26 else ema_21
        macd_line = ema_12 - ema_26
        signal_line = macd_line * 0.85
        macd_hist = macd_line - signal_line

        # 4. Bollinger Bands %B
        sma_20 = float(np.mean(closes[-20:]))
        std_20 = float(np.std(closes[-20:]))
        upper_bb = sma_20 + 2.0 * std_20
        lower_bb = sma_20 - 2.0 * std_20
        last_close = closes[-1]
        pct_b = (last_close - lower_bb) / max(1e-4, (upper_bb - lower_bb))

        # 5. ATR Volatility %
        tr = np.maximum(highs - lows, np.abs(highs - np.roll(closes, 1)))[1:]
        atr = float(np.mean(tr[-14:])) if len(tr) >= 14 else (last_close * 0.008)
        atr_pct = (atr / last_close) * 100.0

        return {
            "rsi_14": round(float(rsi), 2),
            "ema_spread_pct": round(float(ema_spread), 3),
            "macd_hist": round(float(macd_hist), 2),
            "bollinger_pct_b": round(float(pct_b), 3),
            "atr_pct": round(float(atr_pct), 3),
        }

    @classmethod
    def generate_multi_horizon_prediction(
        cls,
        symbol: str,
        current_spot: float,
        candles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesizes features into probabilistic multi-horizon predictions:
        - 15-Minute Scalp Horizon
        - 1-Hour Intraday Horizon
        - End-of-Day (EOD) Swing Horizon
        """
        features = cls.extract_technical_features(candles)
        rsi = features["rsi_14"]
        ema_spread = features["ema_spread_pct"]
        macd_hist = features["macd_hist"]

        # Composite Bullish Score (-100 to +100)
        bullish_score = 0.0
        # RSI contribution
        if rsi < 30:
            bullish_score += 35.0  # Oversold mean reversion
        elif rsi > 70:
            bullish_score -= 35.0  # Overbought mean reversion
        else:
            bullish_score += (rsi - 50.0) * 0.8

        # Momentum contribution
        bullish_score += np.clip(ema_spread * 40.0, -40.0, 40.0)
        bullish_score += np.clip(macd_hist * 2.0, -25.0, 25.0)

        # Probabilities
        prob_bullish = 1.0 / (1.0 + math.exp(-bullish_score / 25.0))
        prob_bearish = 1.0 - prob_bullish

        # Horizon Breakdown
        scalp_bias = "BULLISH" if prob_bullish > 0.55 else ("BEARISH" if prob_bearish > 0.55 else "NEUTRAL")
        intraday_bias = scalp_bias
        eod_bias = "BULLISH" if prob_bullish > 0.52 else ("BEARISH" if prob_bearish > 0.52 else "NEUTRAL")

        # ATR-based target and stop-loss calculations in ₹ INR
        atr_pts = current_spot * (features["atr_pct"] / 100.0)
        if scalp_bias == "BULLISH":
            target_price = round(current_spot + (atr_pts * 1.5), 2)
            stop_loss = round(current_spot - (atr_pts * 0.8), 2)
            action = "ACCUMULATE_CALLS"
        elif scalp_bias == "BEARISH":
            target_price = round(current_spot - (atr_pts * 1.5), 2)
            stop_loss = round(current_spot + (atr_pts * 0.8), 2)
            action = "ACCUMULATE_PUTS"
        else:
            target_price = round(current_spot + (atr_pts * 0.5), 2)
            stop_loss = round(current_spot - (atr_pts * 0.5), 2)
            action = "DEPLOY_IRON_CONDOR"

        risk_reward = round(abs(target_price - current_spot) / max(0.01, abs(current_spot - stop_loss)), 2)

        return {
            "symbol": symbol,
            "current_spot_inr": current_spot,
            "technical_features": features,
            "prob_bullish_pct": round(prob_bullish * 100.0, 1),
            "prob_bearish_pct": round(prob_bearish * 100.0, 1),
            "horizons": {
                "scalp_15m": {"bias": scalp_bias, "confidence_pct": round(max(prob_bullish, prob_bearish) * 100.0, 1)},
                "intraday_1h": {"bias": intraday_bias, "confidence_pct": round(max(prob_bullish, prob_bearish) * 95.0, 1)},
                "eod_swing": {"bias": eod_bias, "confidence_pct": round(max(prob_bullish, prob_bearish) * 90.0, 1)},
            },
            "recommendation": {
                "action": action,
                "target_price_inr": target_price,
                "stop_loss_inr": stop_loss,
                "risk_reward_ratio": risk_reward,
                "max_drawdown_risk_pct": round(features["atr_pct"] * 0.8, 2),
            },
        }


stock_recommender = StockRecommender()
