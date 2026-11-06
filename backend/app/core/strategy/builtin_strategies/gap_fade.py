import logging
from typing import Dict, Any

from ..strategy_lifecycle import ProprietaryStrategyBase, StrategySignal
from ...indicators.indian_ta_library import IndianTALibrary

logger = logging.getLogger(__name__)


class GIFTNiftyGapFade(ProprietaryStrategyBase):
    """
    GIFT Nifty Pre-Open Gap Fade Strategy.
    Capitalizes on overnight international sentiment overreactions.
    Statistical baseline shows ~68% of Indian morning gaps > 0.6% partially or fully fill by 10:45 AM IST.
    """

    strategy_name = "GIFT Nifty Pre-Open Gap Fade"
    min_india_vix = 12.0
    max_india_vix = 24.0
    preferred_session = "MORNING"  # Active 9:15 AM to 11:30 AM IST

    def compute_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        gift_price = float(market_data.get("gift_nifty_price", 24650.0))
        prev_close = float(market_data.get("prev_nse_close", 24500.0))
        current_spot = float(market_data.get("current_price", gift_price))

        gap_signal = IndianTALibrary.gift_nifty_gap_signal(gift_price, prev_close)

        return {
            "gap_signal": gap_signal,
            "prev_close": prev_close,
            "current_spot": current_spot,
            "gap_points": gift_price - prev_close,
            "gap_pct": (gift_price - prev_close) / max(1.0, prev_close),
        }

    def generate_signal(self, indicators: Dict[str, Any], market_data: Dict[str, Any]) -> StrategySignal:
        ticker = market_data.get("ticker", "NIFTY50")
        current_spot = indicators["current_spot"]
        prev_close = indicators["prev_close"]
        gap_pct = indicators["gap_pct"]
        gap_pts = indicators["gap_points"]

        # Fading a substantial gap up
        if gap_pct >= 0.0065:
            entry = current_spot
            stop_loss = round(entry + abs(gap_pts) * 0.45, 2)
            target = round(entry - abs(gap_pts) * 0.75, 2)
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="SELL",
                confidence=0.78,
                entry_price=entry,
                stop_loss=stop_loss,
                target_1=target,
                risk_reward_ratio=1.65,
                rationale=f"Fading massive gap-up of +{gap_pts:.1f} pts (+{gap_pct*100:.2f}%). Targeting mean-reversion fill to previous close ₹{prev_close:,.1f}.",
            )
        # Fading a substantial gap down
        elif gap_pct <= -0.0065:
            entry = current_spot
            stop_loss = round(entry - abs(gap_pts) * 0.45, 2)
            target = round(entry + abs(gap_pts) * 0.75, 2)
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="BUY",
                confidence=0.78,
                entry_price=entry,
                stop_loss=stop_loss,
                target_1=target,
                risk_reward_ratio=1.65,
                rationale=f"Fading severe gap-down of {gap_pts:.1f} pts ({gap_pct*100:.2f}%). Accumulating oversold panic on open.",
            )

        return StrategySignal(
            strategy_name=self.strategy_name,
            ticker=ticker,
            action="HOLD",
            confidence=0.0,
            entry_price=current_spot,
            rationale=f"Gap magnitude ({gap_pct*100:+.2f}%) within standard noise threshold. Standing down.",
        )
