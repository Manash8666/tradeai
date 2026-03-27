"""
Baseline Mean Reversion Model

A statistical baseline model. Instead of deep learning, this uses simple Z-Score
calculations over a rolling window to detect overbought/oversold conditions.
"""

from typing import Any, Dict

import numpy as np
import pandas as pd

from ai_agent.models.base import BaseModel


class BaselineMeanReversion(BaseModel):
    """Z-Score based Mean Reversion model."""

    def __init__(self, window: int = 20, z_threshold: float = 2.0) -> None:
        super().__init__(model_name="BaselineMeanReversion", version="1.0.0")
        self.window = window
        self.z_threshold = z_threshold
        # Statistical models don't have "weights" to load, they are deterministic
        self._is_loaded = True

    def load(self, path: str) -> None:
        pass

    def save(self, path: str) -> None:
        pass

    def predict(self, features: pd.DataFrame | np.ndarray) -> Dict[str, Any]:
        """
        Expects a 1D array or pandas Series representing the closing prices
        of the last `window` ticks/bars.
        """
        if isinstance(features, pd.DataFrame):
            # Assumes 'close' column exists
            prices = features['close'].values
        else:
            prices = np.asarray(features)
            
        if len(prices) < self.window:
            return {
                "signal": "HOLD",
                "confidence": 0.0,
                "metadata": {"reason": "insufficient_data"}
            }

        # Calculate Z-Score of the most recent price
        recent_prices = prices[-self.window:]
        mean_price = np.mean(recent_prices)
        std_price = np.std(recent_prices)
        
        if std_price == 0:
            return {"signal": "HOLD", "confidence": 0.0}

        current_price = prices[-1]
        z_score = (current_price - mean_price) / std_price

        # Z > threshold -> Overbought -> Expect price to fall -> SELL
        # Z < -threshold -> Oversold -> Expect price to rise -> BUY
        if z_score < -self.z_threshold:
            # We are oversold. Confidence scales with how far past threshold we are.
            confidence = min(abs(z_score) / (self.z_threshold * 1.5), 1.0)
            return {
                "signal": "BUY",
                "confidence": confidence,
                "metadata": {"z_score": float(z_score), "mean": float(mean_price)}
            }
            
        elif z_score > self.z_threshold:
            # We are overbought
            confidence = min(abs(z_score) / (self.z_threshold * 1.5), 1.0)
            return {
                "signal": "SELL",
                "confidence": confidence,
                "metadata": {"z_score": float(z_score), "mean": float(mean_price)}
            }
            
        return {
            "signal": "HOLD",
            "confidence": 0.0,
            "metadata": {"z_score": float(z_score)}
        }
