import logging
from typing import Dict, Any

from ..strategy_lifecycle import ProprietaryStrategyBase, StrategySignal
from ...indicators.indian_ta_library import IndianTALibrary

logger = logging.getLogger(__name__)


class FIIFlowFollower(ProprietaryStrategyBase):
    """
    FII Institutional Flow Follower (1 to 3-day Swing Engine).
    Leverages daily 6:30 PM NSE participant-wise derivative reports.
    Executes alongside the foreign fund institutional positioning footprint.
    """

    strategy_name = "FII Institutional Flow Follower"
    min_india_vix = 10.0
    max_india_vix = 25.0
    preferred_session = "FULL"

    def compute_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        fii_futures_net = int(market_data.get("fii_index_futures_net", 10000))
        dii_cash_net_cr = float(market_data.get("dii_net_inflow_cr", 500.0))
        pcr = float(market_data.get("pcr", 0.95))
        current_spot = float(market_data.get("current_price", 24500.0))

        pcr_signal = IndianTALibrary.fii_pcr_signal(pcr)

        return {
            "fii_futures_net": fii_futures_net,
            "dii_cash_net_cr": dii_cash_net_cr,
            "pcr": pcr,
            "pcr_signal": pcr_signal,
            "current_spot": current_spot,
        }

    def generate_signal(self, indicators: Dict[str, Any], market_data: Dict[str, Any]) -> StrategySignal:
        ticker = market_data.get("ticker", "NIFTY50")
        fii_futures_net = indicators["fii_futures_net"]
        current_spot = indicators["current_spot"]
        dii_net_cr = indicators["dii_cash_net_cr"]

        # Strong FII Net Long Exposure (> 6,500 index futures contracts)
        if fii_futures_net >= 6500:
            entry = current_spot
            stop_loss = round(entry * 0.990, 2)  # 1% stop loss
            target = round(entry * 1.025, 2)    # 2.5% swing target
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="BUY",
                confidence=0.84,
                entry_price=entry,
                stop_loss=stop_loss,
                target_1=target,
                risk_reward_ratio=2.5,
                rationale=(
                    f"FII institutional long surge confirmed: Net +{fii_futures_net:,} Index Futures contracts. "
                    f"DII absorbing cash supply (+₹{dii_net_cr:,.0f} Cr). Entering swing long."
                ),
            )
        # Strong FII Net Short Exposure (< -6,500 index futures contracts)
        elif fii_futures_net <= -6500:
            entry = current_spot
            stop_loss = round(entry * 1.010, 2)
            target = round(entry * 0.975, 2)
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="SELL",
                confidence=0.84,
                entry_price=entry,
                stop_loss=stop_loss,
                target_1=target,
                risk_reward_ratio=2.5,
                rationale=(
                    f"FII institutional short positioning heavy: Net {fii_futures_net:,} Index Futures contracts. "
                    f"Initiating defensive swing hedge."
                ),
            )

        return StrategySignal(
            strategy_name=self.strategy_name,
            ticker=ticker,
            action="HOLD",
            confidence=0.0,
            rationale=f"FII index futures positioning ({fii_futures_net:,} contracts) within neutral band [-6500, +6500].",
        )
