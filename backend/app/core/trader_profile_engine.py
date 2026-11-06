import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import zoneinfo

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


@dataclass
class TraderProfile:
    trader_id: str = "DEFAULT_PRO_TRADER"
    risk_tolerance: float = 0.50  # 0.0 (Ultra-Conservative) to 1.0 (Aggressive)
    preferred_instruments: List[str] = field(default_factory=lambda: ["NIFTY_OPTIONS", "BANKNIFTY_OPTIONS", "EQUITY"])
    trading_session_preference: str = "MORNING"  # "MORNING", "AFTERNOON", "FULL_DAY"
    average_holding_period_minutes: float = 25.0
    max_daily_loss_tolerance_inr: float = 15000.0
    daily_profit_target_inr: float = 50000.0
    behavioral_risk_score: float = 0.0  # 0.0 (Clean) to 1.0 (High emotional friction/revenge danger)
    ist_peak_performance_hour: int = 10  # 10:00 AM IST statistically optimal
    total_trades_analyzed: int = 0
    consecutive_losses: int = 0


class TraderProfileEngine:
    """
    N-of-1 Personalized Behavioral & Risk Calibration Engine.
    Continuously monitors trader psychology, detects impulsive revenge-trading tendencies,
    and dynamically enforces tailored position sizing for Indian derivatives.
    """

    def __init__(self, profile: Optional[TraderProfile] = None):
        self.profile = profile or TraderProfile()
        self.recent_trades: List[Dict[str, Any]] = []
        logger.info(f"[TRADER PROFILE] N-of-1 Behavioral Engine calibrated for: {self.profile.trader_id}")

    def update_profile_from_trade(self, trade_result: Dict[str, Any]) -> None:
        """
        Ingests trade outcome, tracking psychological drift and tilt triggers.
        """
        pnl_inr = float(trade_result.get("pnl_inr", 0.0))
        trade_time_str = trade_result.get("timestamp_ist", datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"))
        qty = int(trade_result.get("quantity", 50))

        self.profile.total_trades_analyzed += 1
        self.recent_trades.append({
            "pnl_inr": pnl_inr,
            "quantity": qty,
            "timestamp": trade_time_str,
        })

        if pnl_inr < 0:
            self.profile.consecutive_losses += 1
            # Check for revenge trading risk escalation
            if self.profile.consecutive_losses >= 2:
                self.profile.behavioral_risk_score = min(1.0, self.profile.behavioral_risk_score + 0.25)
                logger.warning(
                    f"[TRADER PROFILE] Revenge trading risk elevated! "
                    f"Consecutive losses: {self.profile.consecutive_losses}, "
                    f"Behavioral Score: {self.profile.behavioral_risk_score:.2f}"
                )
        else:
            self.profile.consecutive_losses = 0
            # Gradually cool down behavioral risk on disciplined winning trades
            self.profile.behavioral_risk_score = max(0.0, self.profile.behavioral_risk_score - 0.10)

    def detect_revenge_trading_pattern(self, recent_trades: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Evaluates whether the trader is escalating quantity after consecutive losses.
        """
        trades = recent_trades or self.recent_trades
        if len(trades) < 3:
            return False

        last_three = trades[-3:]
        two_prior_losses = last_three[0]["pnl_inr"] < 0 and last_three[1]["pnl_inr"] < 0
        qty_escalated = last_three[2]["quantity"] > max(last_three[0]["quantity"], last_three[1]["quantity"])

        is_revenge = two_prior_losses and qty_escalated
        if is_revenge:
            logger.critical("[TRADER PROFILE] ?? REVENGE TRADING PATTERN DETECTED: Loss followed by position escalation.")
        return is_revenge

    def get_personalized_position_size(self, signal_confidence: float, india_vix: float) -> float:
        """
        Calculates recommended capital allocation percentage (0.0% to 10.0%)
        dampened by behavioral tilt score and market volatility.
        """
        base_size = signal_confidence * 8.0 * self.profile.risk_tolerance

        # Tilt dampener: If behavioral risk is high, reduce size dramatically
        tilt_dampener = max(0.20, 1.0 - (self.profile.behavioral_risk_score * 0.70))

        # India VIX dampener
        if india_vix > 22.0:
            vix_dampener = 0.50
        elif india_vix > 18.0:
            vix_dampener = 0.75
        else:
            vix_dampener = 1.00

        recommended_size = round(base_size * tilt_dampener * vix_dampener, 1)
        logger.info(
            f"[TRADER PROFILE] Sizing: {recommended_size}% (Conf: {signal_confidence:.2f}, "
            f"Tilt: {self.profile.behavioral_risk_score:.2f}, VIX: {india_vix:.1f})"
        )
        return recommended_size

    def get_daily_limits(self) -> Dict[str, Any]:
        """Returns personalized daily bounds."""
        return {
            "trader_id": self.profile.trader_id,
            "max_daily_loss_inr": self.profile.max_daily_loss_tolerance_inr,
            "daily_profit_target_inr": self.profile.daily_profit_target_inr,
            "behavioral_risk_score": self.profile.behavioral_risk_score,
            "is_tilted": self.profile.behavioral_risk_score > 0.5,
            "recommended_max_trades_per_day": 8 if self.profile.behavioral_risk_score < 0.3 else 3,
        }
