"""
RL Manager (Profit/Loss Manager)
=================================
Manages dynamic trailing stop-losses using ATR (Average True Range).
Also provides the scaffold for the Reinforcement Learning agent (PPO/A2C)
that controls execution sizing based on environmental rewards.
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)


class RLManager:
    """Handles ATR-based dynamic stop-loss and stub for RL-driven sizing."""

    def __init__(self, atr_multiplier: float = 2.0):
        self.atr_multiplier = atr_multiplier
        # In a full deployment, load stable-baselines3 PPO model here
        self._ppo_model = None
        logger.info("RLManager initialized with ATR multiplier %.2f", atr_multiplier)

    def calculate_trailing_stop(self, current_price: float, df: pd.DataFrame) -> float:
        """
        Calculates a dynamic stop-loss using the ATR indicator natively.
        `df` must contain High, Low, Close columns.
        """
        if len(df) < 14:
            # Fallback to fixed 2% if not enough data
            return current_price * 0.98

        # Calculate True Range natively
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift()).abs()
        low_close = (df["Low"] - df["Close"].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Calculate ATR(14) using exponential moving average
        atr = tr.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()

        current_atr = float(atr.iloc[-1])
        stop_level = current_price - (current_atr * self.atr_multiplier)

        logger.debug("Calculated Trailing Stop: %.2f (ATR=%.2f)", stop_level, current_atr)
        return stop_level

    def predict_action(self, market_state: dict) -> str:
        """
        Stub for RL PPO inference: predict 'Buy/Hold/Sell/Rotate'.
        """
        # Placeholder logic: mapping simple state to action
        return "Hold"
