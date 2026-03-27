from datetime import datetime
import zoneinfo
import logging

logger = logging.getLogger(__name__)


class ISTTimezoneGuard:
    """
    FATAL FLAW PREVENTION: UTC / Server-Local Timezone Slippage.

    The Indian Stock Market (NSE/BSE) operates on IST (UTC+5:30). If the trading
    server is deployed on a standard AWS `us-east-1` EC2 instance, calling
    `datetime.now()` returns UTC time (5.5 hours behind India).

    If the Hero-Zero Gamma Engine triggers an "End-of-Day 3:00 PM" option explosion
    using server time, it will execute in the middle of the Indian night, failing,
    or worse, executing mid-day the next morning resulting in absolute catastrophic
    capital permanent loss.
    """

    def __init__(self):
        try:
            self.ist_zone = zoneinfo.ZoneInfo("Asia/Kolkata")
            logger.info(
                "[TIMEZONE GUARD] Activated. All temporal matrices strictly bound to Asia/Kolkata (UTC+5:30). Server local-time dependencies eradicated."  # noqa: E501
            )
        except Exception as e:
            logger.error(f"[FATAL] Cannot load Asia/Kolkata timezone: {e}")
            raise e

    def get_market_time(self) -> datetime:
        """Returns the absolute exact IST time regardless of AWS server deployment region."""
        return datetime.now(self.ist_zone)

    def is_market_open(self) -> bool:
        """Strictly validates 9:15 AM to 3:30 PM IST boundaries natively."""
        now = self.get_market_time()

        # Prevent weekend trading loops
        if now.weekday() >= 5:  # 5=Sat, 6=Sun
            return False

        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_start <= now <= market_end

    def time_to_expiry_charm_decay(self) -> float:
        """
        Calculates exact minutes remaining to 3:30 PM IST for PDE Gamma/Charm models.
        """
        now = self.get_market_time()
        market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)

        if now > market_end:
            return 0.0

        diff = market_end - now
        return diff.total_seconds() / 60.0


temporal_guard = ISTTimezoneGuard()
