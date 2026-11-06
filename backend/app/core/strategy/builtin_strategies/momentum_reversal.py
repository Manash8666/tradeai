import logging
from typing import Dict, Any
import numpy as np

from ..strategy_lifecycle import ProprietaryStrategyBase, StrategySignal
from ...indicators.indian_ta_library import IndianTALibrary

logger = logging.getLogger(__name__)


class BankNiftyMomentumReversal(ProprietaryStrategyBase):
    """
    BankNifty Intraday Momentum Mean-Reversion Strategy.
    Exploits overextended moves (>0.8% in 5m) where retail stops get triggered
    and market-makers pull liquidity, yielding a fast 50-60% snapback reversion.
    """

    strategy_name = "BankNifty Intraday Momentum Reversal"
    min_india_vix = 11.0
    max_india_vix = 23.0
    preferred_session = "FULL"

    def compute_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        closes = np.asarray(market_data.get("closes_5m", [50000.0] * 20), dtype=float)
        highs = np.asarray(market_data.get("highs_5m", [50100.0] * 20), dtype=float)
        lows = np.asarray(market_data.get("lows_5m", [49900.0] * 20), dtype=float)

        rsi_series = IndianTALibrary.rsi(closes, 14)
        atr_series = IndianTALibrary.atr(highs, lows, closes, 14)

        current_rsi = float(rsi_series[-1]) if len(rsi_series) > 0 else 50.0
        current_atr = float(atr_series[-1]) if len(atr_series) > 0 else 120.0

        # Calculate 5-minute price expansion
        pct_expansion = 0.0
        if len(closes) >= 2:
            pct_expansion = (closes[-1] - closes[-2]) / max(1.0, closes[-2])

        return {
            "rsi": current_rsi,
            "atr": current_atr,
            "pct_expansion": pct_expansion,
            "current_price": float(closes[-1]),
        }

    def generate_signal(self, indicators: Dict[str, Any], market_data: Dict[str, Any]) -> StrategySignal:
        ticker = market_data.get("ticker", "BANKNIFTY")
        current_price = indicators["current_price"]
        rsi = indicators["rsi"]
        atr = indicators["atr"]
        expansion = indicators["pct_expansion"]

        # Mean-reversion conditions
        if rsi >= 76.0 and expansion >= 0.007:  # Severe overbought spike
            entry = current_price
            stop_loss = round(entry + 1.4 * atr, 2)
            target = round(entry - 2.1 * atr, 2)
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="SELL",
                confidence=0.82,
                entry_price=entry,
                stop_loss=stop_loss,
                target_1=target,
                risk_reward_ratio=1.5,
                rationale=f"BankNifty RSI overbought at {rsi:.1f} with +{expansion*100:.2f}% spike. Shorting mean reversion.",
            )
        elif rsi <= 24.0 and expansion <= -0.007:  # Severe oversold dump
            entry = current_price
            stop_loss = round(entry - 1.4 * atr, 2)
            target = round(entry + 2.1 * atr, 2)
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="BUY",
                confidence=0.82,
                entry_price=entry,
                stop_loss=stop_loss,
                target_1=target,
                risk_reward_ratio=1.5,
                rationale=f"BankNifty RSI oversold at {rsi:.1f} with {expansion*100:.2f}% dump. Buying bounce back to VWAP.",
            )

        return StrategySignal(
            strategy_name=self.strategy_name,
            ticker=ticker,
            action="HOLD",
            confidence=0.0,
            entry_price=current_price,
            rationale=f"BankNifty in normal oscillation band (RSI: {rsi:.1f}). No statistical anomaly.",
        )
