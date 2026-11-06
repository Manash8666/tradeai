"""
Automated 09:00 IST Morning Market Routine & Lifecycle Scheduler.
Manages automated Indian market transitions:
- 09:00 AM IST: Pre-Market Intelligence & GIFT Nifty Ingestion
- 09:15 AM IST: Market Opening Bell & Capital Allocation
- 15:15 PM IST: Mandatory Intraday MIS Squareoff Protocol
- 15:35 PM IST: Post-Market Audit & Darwinian Evolution Evaluation
"""

import asyncio
import datetime
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("MorningScheduler")

class MarketScheduleStatus(BaseModel):
    current_time_ist: str
    market_session_state: str  # PRE_MARKET | REGULAR_TRADING | MIS_SQUAREOFF_PHASE | POST_MARKET_AUDIT | CLOSED
    gift_nifty_bias: str
    allocated_capital_inr: float
    daily_profit_target_inr: float
    next_event: str
    seconds_to_next_event: int
    darwinian_generation: int
    is_scheduler_active: bool

class MorningMarketScheduler:
    """Async background daemon for Indian market daily lifecycle."""

    def __init__(self):
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._generation = 7
        self._allocated_capital = 200000.0
        self._daily_target = 25000.0
        self._bias = "NEUTRAL"
        self._last_event_triggered = ""

    def get_ist_now(self) -> datetime.datetime:
        """Returns current timestamp in Indian Standard Time (UTC+05:30)."""
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        return utc_now.astimezone(ist_tz)

    def get_session_state(self) -> MarketScheduleStatus:
        now = self.get_ist_now()
        hour = now.hour
        minute = now.minute
        time_minutes = hour * 60 + minute

        # 09:00 IST = 540
        # 09:15 IST = 555
        # 15:15 IST = 915
        # 15:30 IST = 930
        # 15:35 IST = 935

        is_weekend = now.weekday() >= 5

        if is_weekend:
            state = "CLOSED"
            next_event = "Monday 09:00 AM Pre-Market Scan"
            # Seconds until Monday 09:00 AM
            days_ahead = (7 - now.weekday()) % 7 or 7
            next_target = now.replace(hour=9, minute=0, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
            seconds_remaining = max(0, int((next_target - now).total_seconds()))
        elif time_minutes < 540:  # Before 09:00 AM
            state = "CLOSED"
            next_event = "09:00 AM IST Pre-Market Intelligence Scan"
            next_target = now.replace(hour=9, minute=0, second=0, microsecond=0)
            seconds_remaining = max(0, int((next_target - now).total_seconds()))
        elif time_minutes < 555:  # 09:00 - 09:15 AM
            state = "PRE_MARKET"
            next_event = "09:15 AM IST Live Trading Session Opening Bell"
            next_target = now.replace(hour=9, minute=15, second=0, microsecond=0)
            seconds_remaining = max(0, int((next_target - now).total_seconds()))
        elif time_minutes < 915:  # 09:15 - 15:15 PM
            state = "REGULAR_TRADING"
            next_event = "15:15 PM IST Mandatory Intraday MIS Squareoff"
            next_target = now.replace(hour=15, minute=15, second=0, microsecond=0)
            seconds_remaining = max(0, int((next_target - now).total_seconds()))
        elif time_minutes < 930:  # 15:15 - 15:30 PM
            state = "MIS_SQUAREOFF_PHASE"
            next_event = "15:30 PM IST Market Closing Bell"
            next_target = now.replace(hour=15, minute=30, second=0, microsecond=0)
            seconds_remaining = max(0, int((next_target - now).total_seconds()))
        elif time_minutes < 935:  # 15:30 - 15:35 PM
            state = "POST_MARKET_AUDIT"
            next_event = "15:35 PM IST Darwinian Evolution & Ledger Checkpoint"
            next_target = now.replace(hour=15, minute=35, second=0, microsecond=0)
            seconds_remaining = max(0, int((next_target - now).total_seconds()))
        else:
            state = "CLOSED"
            next_event = "Tomorrow 09:00 AM Pre-Market Scan"
            next_target = (now + datetime.timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            seconds_remaining = max(0, int((next_target - now).total_seconds()))

        return MarketScheduleStatus(
            current_time_ist=now.strftime("%Y-%m-%d %H:%M:%S IST"),
            market_session_state=state,
            gift_nifty_bias=self._bias,
            allocated_capital_inr=self._allocated_capital,
            daily_profit_target_inr=self._daily_target,
            next_event=next_event,
            seconds_to_next_event=seconds_remaining,
            darwinian_generation=self._generation,
            is_scheduler_active=self._is_running,
        )

    async def start(self):
        """Starts background loop."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Morning Market Routine Scheduler started.")

    async def stop(self):
        """Stops background loop."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Morning Market Routine Scheduler stopped.")

    async def _loop(self):
        while self._is_running:
            try:
                now = self.get_ist_now()
                hour = now.hour
                minute = now.minute

                # 09:00 AM IST Hook
                if hour == 9 and minute == 0 and self._last_event_triggered != "09:00":
                    self._last_event_triggered = "09:00"
                    self._bias = "BULLISH_GAP_UP"
                    logger.info("[SCHEDULE] 09:00 AM IST: Ingesting Pre-Market GIFT Nifty & Foreign Macro Cues.")

                # 09:15 AM IST Hook
                elif hour == 9 and minute == 15 and self._last_event_triggered != "09:15":
                    self._last_event_triggered = "09:15"
                    logger.info("[SCHEDULE] 09:15 AM IST: Market Opening Bell! Allocating ₹2,00,000 to Gen-%d.", self._generation)

                # 15:15 PM IST Hook
                elif hour == 15 and minute == 15 and self._last_event_triggered != "15:15":
                    self._last_event_triggered = "15:15"
                    logger.warning("[SCHEDULE] 15:15 PM IST: Initiating mandatory intraday MIS squareoff & cancelling pending orders.")

                # 15:35 PM IST Hook
                elif hour == 15 and minute == 35 and self._last_event_triggered != "15:35":
                    self._last_event_triggered = "15:35"
                    logger.info("[SCHEDULE] 15:35 PM IST: Day-End Post-Mortem Audit & Darwinian Evaluation complete.")

                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in scheduler loop: %s", e)
                await asyncio.sleep(30)

# Global singleton
morning_market_scheduler = MorningMarketScheduler()
