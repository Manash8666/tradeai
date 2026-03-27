"""
Pre-Trade Risk Management Engine

This is a mandatory interceptor sitting between strategy execution and broker dispatch.
It enforces Max Drawdown, Leverage, and Fat-Finger metrics. If any rule is violated,
a `RiskViolationException` is thrown before the capital is ever put at risk.
"""

import logging
from typing import Any, Dict

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RiskViolationException(Exception):
    """Raised when an order violates risk parameters."""
    pass


class RiskConfig(BaseModel):
    """Risk boundaries."""
    max_daily_drawdown_pct: float = Field(0.05, description="Max 5% account decline")
    max_position_size_pct: float = Field(0.20, description="Max 20% equity in one symbol")
    max_single_order_qty: int = Field(1000, description="Fat-finger prevention")


class AccountState(BaseModel):
    """Snapshot of account equity and margins."""
    net_liquidity: float = 100_000.0  # ₹1 Lakh simulated
    start_of_day_equity: float = 100_000.0
    reserved_margin: float = 0.0


class RiskManager:
    """Pre-Trade validation engine."""

    def __init__(self, config: RiskConfig | None = None) -> None:
        self.config = config or RiskConfig()
        self.account = AccountState()
        self.daily_pnl = 0.0
        logger.info(f"RiskManager initialized | Drawdown Limit: {self.config.max_daily_drawdown_pct*100}%")

    def validate_pre_trade(self, symbol: str, side: str, qty: int, price: float, current_exposure: float) -> bool:
        """
        Evaluate risk limits on an impending order.
        
        Args:
            symbol: Ticker
            side: 'BUY' or 'SELL'
            qty: Quantity to trade
            price: Expected fill price
            current_exposure: Total currency allocated to this ticker currently
            
        Raises:
            RiskViolationException: If order breaches risk bounds.
        """
        order_value = qty * price

        # 1. Fat Finger Check
        if qty <= 0 or qty > self.config.max_single_order_qty:
            logger.error(f"[RISK REJECT] Fat Finger Violation: Qty {qty} exceeds {self.config.max_single_order_qty}")
            raise RiskViolationException(f"Order quantity {qty} exceeds max limit.")

        # 2. Daily Drawdown Rule
        drawdown_pct = (self.account.start_of_day_equity - self.account.net_liquidity) / self.account.start_of_day_equity
        if drawdown_pct >= self.config.max_daily_drawdown_pct:
            logger.error(f"[RISK REJECT] Max Drawdown reached: {drawdown_pct*100:.2f}% (Limit: {self.config.max_daily_drawdown_pct*100}%)")
            raise RiskViolationException(f"Account hits Max Daily Drawdown hard stop.")

        # 3. Position Sizing Rule
        projected_exposure = current_exposure + (order_value if side.upper() == "BUY" else -order_value)
        exposure_pct = abs(projected_exposure) / self.account.net_liquidity
        
        if exposure_pct > self.config.max_position_size_pct:
            logger.error(f"[RISK REJECT] Position Size Violation on {symbol}. {exposure_pct*100:.1f}% > {self.config.max_position_size_pct*100}%")
            raise RiskViolationException(f"Order puts exposure heavily outside allowed capital limits.")

        logger.debug(f"[RISK APPROVED] Order {side} {qty} {symbol} passed validations.")
        return True

    def update_pnl(self, current_equity: float) -> None:
        """Update intra-day net liquidity for accurate drawdown calculation."""
        self.account.net_liquidity = current_equity

# Global Singleton Hook
risk_manager = RiskManager()
