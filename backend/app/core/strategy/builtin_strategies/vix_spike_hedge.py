import logging
from typing import Dict, Any

from ..strategy_lifecycle import ProprietaryStrategyBase, StrategySignal
from ...indicators.indian_ta_library import IndianTALibrary

logger = logging.getLogger(__name__)


class IndiaVIXSpikeHedge(ProprietaryStrategyBase):
    """
    India VIX Spike Defensive Hedge Strategy.
    Activates when volatility surges above 19.5 to deploy protective asymmetric ATM put options,
    insulating long portfolio delta against catastrophic drawdowns (e.g. election or geopolitical shocks).
    """

    strategy_name = "India VIX Spike Defensive Hedge"
    min_india_vix = 19.5
    max_india_vix = 45.0
    preferred_session = "FULL"

    def compute_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        india_vix = float(market_data.get("india_vix", 20.5))
        vix_signal = IndianTALibrary.india_vix_regime(india_vix)
        portfolio_val = float(market_data.get("portfolio_value_inr", 1_000_000.0))
        current_spot = float(market_data.get("current_price", 24500.0))

        return {
            "india_vix": india_vix,
            "vix_signal": vix_signal,
            "portfolio_value_inr": portfolio_val,
            "current_spot": current_spot,
        }

    def generate_signal(self, indicators: Dict[str, Any], market_data: Dict[str, Any]) -> StrategySignal:
        ticker = market_data.get("ticker", "NIFTY50")
        india_vix = indicators["india_vix"]
        current_spot = indicators["current_spot"]
        portfolio_val = indicators["portfolio_value_inr"]

        # 1 lot per ₹5 Lakh portfolio value sizing heuristic
        lots_to_hedge = max(1, int(portfolio_val / 500_000.0))

        if india_vix >= 22.0:
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="HEDGE_BUY",
                confidence=0.92,
                entry_price=current_spot,
                stop_loss=None,  # Defined-risk option long hedge
                target_1=round(current_spot * 0.96, 2),
                risk_reward_ratio=3.0,
                rationale=(
                    f"CRITICAL VOLATILITY SURGE: India VIX at {india_vix:.1f}. "
                    f"Deploying {lots_to_hedge} lots of ATM Nifty Put protection to preserve ₹{portfolio_val:,.0f} portfolio value."
                ),
            )
        elif india_vix >= 19.5:
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="HEDGE_BUY",
                confidence=0.70,
                entry_price=current_spot,
                stop_loss=None,
                target_1=round(current_spot * 0.98, 2),
                risk_reward_ratio=2.0,
                rationale=f"Elevated India VIX ({india_vix:.1f}). Purchasing partial delta hedge (50% coverage).",
            )

        return StrategySignal(
            strategy_name=self.strategy_name,
            ticker=ticker,
            action="HOLD",
            confidence=0.0,
            rationale=f"India VIX {india_vix:.1f} within safe zone. No defensive hedge required.",
        )
