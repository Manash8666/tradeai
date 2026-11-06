import logging
from typing import Dict, Any

from ..strategy_lifecycle import ProprietaryStrategyBase, StrategySignal
from ...indicators.indian_ta_library import IndianTALibrary

logger = logging.getLogger(__name__)


class ExpiryGammaSqueeze(ProprietaryStrategyBase):
    """
    0DTE Expiry Gamma Squeeze Strategy.
    Capitalizes on extreme Gamma sensitivity after 1:45 PM IST on daily index expiry sessions.
    Identifies trapped writers when spot pierces heavy Call/Put Open Interest boundaries.
    """

    strategy_name = "0DTE Expiry Gamma Squeeze"
    min_india_vix = 11.0
    max_india_vix = 26.0
    preferred_session = "AFTERNOON"  # 1:00 PM to 3:15 PM IST

    def compute_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        weekday = int(market_data.get("weekday", 3))  # Thursday default (Nifty expiry)
        days_to_expiry = int(market_data.get("days_to_expiry", 0))
        current_spot = float(market_data.get("current_price", 24500.0))
        vwap_val = float(market_data.get("vwap", current_spot))
        pcr = float(market_data.get("pcr", 1.0))

        expiry_info = IndianTALibrary.expiry_week_indicator(weekday, days_to_expiry)

        return {
            "expiry_info": expiry_info,
            "days_to_expiry": days_to_expiry,
            "current_spot": current_spot,
            "vwap": vwap_val,
            "pcr": pcr,
            "is_above_vwap": current_spot > vwap_val,
        }

    def generate_signal(self, indicators: Dict[str, Any], market_data: Dict[str, Any]) -> StrategySignal:
        ticker = market_data.get("ticker", "NIFTY50")
        current_spot = indicators["current_spot"]
        vwap = indicators["vwap"]
        pcr = indicators["pcr"]
        days_to_expiry = indicators["days_to_expiry"]

        if days_to_expiry != 0:
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="HOLD",
                confidence=0.0,
                rationale="Gamma Squeeze engine exclusively activates on 0DTE settlement sessions.",
            )

        # Bullish Gamma Squeeze: Spot pushing well above VWAP with rising PCR
        if indicators["is_above_vwap"] and pcr > 1.15:
            entry = current_spot
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="BUY",
                confidence=0.86,
                entry_price=entry,
                stop_loss=round(vwap - 15.0, 2),
                target_1=round(entry + 65.0, 2),
                risk_reward_ratio=2.2,
                rationale=(
                    f"0DTE Bullish Gamma Squeeze detected on {ticker}. Spot (₹{current_spot:,.1f}) accelerating above "
                    f"VWAP (₹{vwap:,.1f}) with Call writers trapped into short-covering panic."
                ),
            )
        # Bearish Gamma Squeeze: Spot breaking below VWAP with falling PCR
        elif not indicators["is_above_vwap"] and pcr < 0.85:
            entry = current_spot
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=ticker,
                action="SELL",
                confidence=0.86,
                entry_price=entry,
                stop_loss=round(vwap + 15.0, 2),
                target_1=round(entry - 65.0, 2),
                risk_reward_ratio=2.2,
                rationale=(
                    f"0DTE Bearish Gamma Trap detected on {ticker}. Spot (₹{current_spot:,.1f}) tumbling below "
                    f"VWAP (₹{vwap:,.1f}) triggering forced liquidation from Put writers."
                ),
            )

        return StrategySignal(
            strategy_name=self.strategy_name,
            ticker=ticker,
            action="HOLD",
            confidence=0.0,
            rationale="0DTE Gamma dynamics balanced around pin strike. Standing aside.",
        )
