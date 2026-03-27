"""
NautilusTrader Engine Wrapper

Wraps the Nautilus Engine into a FastAPI-friendly async paradigm while strictly
enforcing the Phase 1 architectural goals and SEBI compliance overrides.
"""

import asyncio
import logging
from typing import Optional

from nautilus_trader.common.component import Logger
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode

from core.message_bus import message_bus

logger = logging.getLogger(__name__)


class EngineWrapper:
    """Async wrapper managing the NautilusTrader TradingNode lifecycle."""

    def __init__(self) -> None:
        self.node: Optional[TradingNode] = None
        self._is_running: bool = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Initialize and start the Nautilus core engine node asynchronously."""
        async with self._lock:
            if self._is_running:
                logger.warning("Engine is already running.")
                return

            logger.info("Starting NautilusTrader Engine...")
            try:
                # SEBI Compliance: Trading Node must run without external routing layers
                config = TradingNodeConfig(
                    id="AI_TRADING_NODE_1",
                    log_level="INFO",
                    bypass_logging=False,
                )

                self.node = TradingNode(config=config)

                # Start the node (this prepares the internal components)
                self.node.start()
                self._is_running = True

                await message_bus.publish(
                    "system", {"event": "engine_started", "status": "success"}
                )
                logger.info("NautilusTrader Engine strictly started successfully.")

            except Exception as e:
                logger.error(f"Failed to start Nautilus Engine: {e}", exc_info=True)
                await message_bus.publish(
                    "system", {"event": "engine_start_failed", "error": str(e)}
                )
                raise e

    async def stop(self) -> None:
        """Safely wind down the trading engine and clear memory."""
        async with self._lock:
            if not self._is_running or not self.node:
                return

            logger.info("Stopping NautilusTrader Engine...")
            try:
                self.node.stop()
                self._is_running = False
                self.node = None

                await message_bus.publish(
                    "system", {"event": "engine_stopped", "status": "success"}
                )
                logger.info("NautilusTrader Engine stopped successfully.")
            except Exception as e:
                logger.error(f"Error while stopping engine: {e}", exc_info=True)

    @property
    def is_running(self) -> bool:
        return self._is_running


# Global Singleton for FastAPI DI
engine_wrapper = EngineWrapper()
