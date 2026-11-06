import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

from backend.app.core.timezone_guards import temporal_guard
from backend.app.core.pnl_greed_lock import greed_lock_engine
from backend.app.core.sebi_ptrc_killswitch import sebi_fortress

logger = logging.getLogger(__name__)


@dataclass
class StrategySignal:
    strategy_name: str
    ticker: str
    action: str  # "BUY", "SELL", "HOLD", "HEDGE_BUY"
    confidence: float  # 0.0 to 1.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    risk_reward_ratio: float = 0.0
    rationale: str = ""
    sebi_compliant: bool = True
    rejection_reason: Optional[str] = None


class ProprietaryStrategyBase(ABC):
    """
    Standardized Lifecycle Container for all Proprietary Indian Strategies.
    Enforces SEBI Pre-Trade Risk Checks (PTRC), Greed Circuit Breaker boundaries,
    and market-hour windowing natively before releasing any execution advice.
    """

    strategy_name: str = "BaseStrategy"
    min_india_vix: float = 0.0
    max_india_vix: float = 30.0
    preferred_session: str = "FULL"  # "MORNING", "AFTERNOON", "FULL"

    @abstractmethod
    def compute_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute mathematical inputs from OHLCV and market matrices."""
        pass

    @abstractmethod
    def generate_signal(self, indicators: Dict[str, Any], market_data: Dict[str, Any]) -> StrategySignal:
        """Derive actionable tactical signals from computed indicators."""
        pass

    def is_active_session(self, hour_ist: int, minute_ist: int) -> bool:
        """Validates if the current IST time aligns with this strategy's preferred volatility window."""
        time_minutes = hour_ist * 60 + minute_ist
        if self.preferred_session == "MORNING":
            return 9 * 60 + 15 <= time_minutes <= 11 * 60 + 30
        elif self.preferred_session == "AFTERNOON":
            return 13 * 60 <= time_minutes <= 15 * 60 + 15
        return 9 * 60 + 15 <= time_minutes <= 15 * 60 + 20

    def validate_sebi_compliance(self, signal: StrategySignal, market_data: Dict[str, Any]) -> bool:
        """
        Validates the generated advisory signal against SEBI PTRC regulations:
        1. Master Kill Switch status.
        2. Psychological Greed Lock check.
        3. BankNifty / Nifty freeze quantity ceiling.
        4. Margin utilization ceiling (85%).
        """
        if sebi_fortress.kill_switch_engaged:
            signal.sebi_compliant = False
            signal.rejection_reason = "SEBI Master Kill Switch is currently engaged."
            return False

        if not greed_lock_engine.can_execute_trade():
            signal.sebi_compliant = False
            signal.rejection_reason = f"Greed Circuit Breaker active: {greed_lock_engine.lock_reason}."
            return False

        qty = int(market_data.get("qty", 0))
        symbol = str(market_data.get("ticker", "")).upper()
        if "BANKNIFTY" in symbol and qty > 900:
            signal.sebi_compliant = False
            signal.rejection_reason = f"Quantity {qty} exceeds SEBI BankNifty freeze quantity limit (900)."
            return False

        avail_margin = float(market_data.get("available_margin", 1_000_000.0))
        req_margin = float(market_data.get("required_margin", 200_000.0))
        if avail_margin > 0 and (req_margin / avail_margin) > 0.85:
            signal.sebi_compliant = False
            signal.rejection_reason = "SEBI PTRC: Required margin exceeds 85% capital allocation cap."
            return False

        signal.sebi_compliant = True
        return True

    def run(self, market_data: Dict[str, Any]) -> StrategySignal:
        """Full pipeline: market check -> indicators -> signal generation -> SEBI validation."""
        now = temporal_guard.get_market_time()

        # Session validity check
        if not self.is_active_session(now.hour, now.minute):
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=market_data.get("ticker", "UNKNOWN"),
                action="HOLD",
                confidence=0.0,
                rationale=f"Outside preferred trading session ({self.preferred_session}).",
                sebi_compliant=True,
            )

        # Volatility envelope check
        current_vix = float(market_data.get("india_vix", 14.5))
        if current_vix < self.min_india_vix or current_vix > self.max_india_vix:
            return StrategySignal(
                strategy_name=self.strategy_name,
                ticker=market_data.get("ticker", "UNKNOWN"),
                action="HOLD",
                confidence=0.0,
                rationale=f"India VIX {current_vix:.1f} outside permissible envelope [{self.min_india_vix}, {self.max_india_vix}].",
                sebi_compliant=True,
            )

        indicators = self.compute_indicators(market_data)
        signal = self.generate_signal(indicators, market_data)
        self.validate_sebi_compliance(signal, market_data)

        logger.info(f"[{self.strategy_name}] Signal: {signal.action} for {signal.ticker} (Compliant: {signal.sebi_compliant})")
        return signal
