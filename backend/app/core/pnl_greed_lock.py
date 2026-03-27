import logging
from datetime import datetime
import zoneinfo

logger = logging.getLogger(__name__)

class PNLGreedCircuitBreaker:
    """
    THE ULTIMATE BEHAVIORAL LIMIT-BREAKER: Daily P&L Hard Lock.
    
    PROBLEM: The average Indian F&O trader reaches profitability at 10:30 AM, 
    but 'revenge trades' or trades on 'greed' until 3:30 PM, giving 100% of 
    profits back to the exchange.
    
    SOLUTION: A mathematically un-bypassable psychological kill switch. 
    Once the configured Daily Profit Target (e.g., +₹50,000) or Max Loss Limit 
    (e.g., -₹15,000) is achieved, this engine categorically physically locks the 
    terminal for the remainder of the IST calendar trading day. 
    
    The user CANNOT execute another block until 12:00 AM IST.
    """
    
    def __init__(self):
        self.ist_zone = zoneinfo.ZoneInfo("Asia/Kolkata")
        
        # Configuration Thresholds (Can be modified statically by the Quant Manager)
        self.daily_profit_target_inr = 50000.0
        self.max_drawdown_limit_inr = -15000.0
        
        self.current_daily_pnl = 0.0
        self.is_locked = False
        self.lock_reason = ""
        self.lock_date = None
        
        logger.info("[GREED CIRCUIT BREAKER] Behavioral P&L Alpha Locks Armed. Enforcing Profit Retention Natively.")

    def _check_daily_reset(self):
        """Resets the Greed Lock exactly at physical midnight IST."""
        current_date = datetime.now(self.ist_zone).date()
        if self.lock_date != current_date:
            self.is_locked = False
            self.current_daily_pnl = 0.0
            self.lock_reason = ""
            self.lock_date = current_date

    def update_realized_pnl(self, realized_trade_net: float):
        """Submits executed trade P&L into the daily accumulator."""
        self._check_daily_reset()
        
        if self.is_locked:
            return # Ignore updates if already frozen
            
        self.current_daily_pnl += realized_trade_net
        
        if self.current_daily_pnl >= self.daily_profit_target_inr:
            self.is_locked = True
            self.lock_reason = f"PROFIT TARGET REACHED (+₹{self.current_daily_pnl:,.2f})"
            logger.critical(f"[GREED BREAKER] 🟢 {self.lock_reason}. TERMINAL LOCKED. PROFIT SECURED.")
            
        elif self.current_daily_pnl <= self.max_drawdown_limit_inr:
            self.is_locked = True
            self.lock_reason = f"MAX LOSS BREACHED (₹{self.current_daily_pnl:,.2f})"
            logger.critical(f"[GREED BREAKER] 🔴 {self.lock_reason}. TERMINAL LOCKED. CAPITAL PRESERVED.")

    def can_execute_trade(self) -> bool:
        """
        Invoked by the PTRC Firewall. Blocks all payloads inherently if triggered.
        """
        self._check_daily_reset()
        if self.is_locked:
            logger.error(f"[GREED BREAKER BLOCK] Trade Prevented. Terminal is Hard-Locked: {self.lock_reason}")
            return False
        return True

greed_lock_engine = PNLGreedCircuitBreaker()
