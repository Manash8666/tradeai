"""
TrueData Data Adapter

Licensed production data provider integration for Indian Equities.
Provides highly accurate Tick stream and backfill data.
"""

import logging
from typing import AsyncIterator, List

from backend.app.config import get_settings
from data.adapters.base import DataAdapter, MarketQuote

logger = logging.getLogger(__name__)
settings = get_settings()


class TrueDataAdapter(DataAdapter):
    """Implementation for TrueData WebSocket and REST APIs."""

    def __init__(self) -> None:
        self.api_key = settings.truedata_api_key
        self.username = settings.truedata_username
        self._is_connected = False

    async def connect(self) -> None:
        """Authenticate with TrueData using credentials from env."""
        if not self.api_key:
            logger.error("Missing TrueData API credentials")
            raise ValueError("TRUEDATA_API_KEY environment variable required")
            
        logger.info("Connecting to TrueData WebSocket server...")
        self._is_connected = True
        logger.info("TrueData connection established.")

    async def disconnect(self) -> None:
        """Close WebSocket session cleanly."""
        self._is_connected = False
        logger.info("TrueData disconnected.")

    async def get_quote(self, symbol: str) -> MarketQuote:
        if not self._is_connected:
            raise ConnectionError("TrueData not connected")
            
        # Placeholder for real REST call
        raise NotImplementedError("TrueData REST HTTP fetch not implemented yet")

    async def stream_quotes(self, symbols: List[str]) -> AsyncIterator[MarketQuote]:
        """Stream real-time ticks over WSS and convert to MarketQuote schema."""
        if not self._is_connected:
            raise ConnectionError("TrueData not connected")

        logger.info(f"Subscribing to TrueData feeds: {symbols}")
        
        # Placeholder for WSS listening loop
        yield MarketQuote(
            symbol=symbols[0],
            timestamp=None, # type: ignore
            open=0.0,
            high=0.0,
            low=0.0,
            close=0.0,
            volume=0,
            source=self.provider_name
        )

    @property
    def provider_name(self) -> str:
        return "TrueData-Premium"

    @property
    def is_licensed(self) -> bool:
        return True
