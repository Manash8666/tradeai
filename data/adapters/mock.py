"""
Mock Data Adapter

Synthetic market data generator for development and paper trading without
consuming licensed API limits.
"""

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import AsyncIterator, List

from data.adapters.base import DataAdapter, MarketQuote

logger = logging.getLogger(__name__)


class DevDataAdapter(DataAdapter):
    """Generates mock market data for local development."""

    def __init__(self) -> None:
        self._is_connected = False
        self._base_prices = {
            "RELIANCE": 2900.0,
            "TCS": 3950.0,
            "HDFCBANK": 1400.0,
            "NIFTY50": 22000.0,
        }

    async def connect(self) -> None:
        self._is_connected = True
        logger.info("Connected to Mock Data Provider")

    async def disconnect(self) -> None:
        self._is_connected = False
        logger.info("Disconnected from Mock Data Provider")

    async def get_quote(self, symbol: str) -> MarketQuote:
        if not self._is_connected:
            raise ConnectionError("DataAdapter not connected")

        base_price = self._base_prices.get(symbol, 1000.0)
        # Random walk +/- 0.5%
        volatility = base_price * 0.005
        current_price = base_price + random.uniform(-volatility, volatility)

        return MarketQuote(
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            open=current_price - 2.0,
            high=current_price + 5.0,
            low=current_price - 5.0,
            close=current_price,
            volume=random.randint(1000, 50000),
            source=self.provider_name,
        )

    async def stream_quotes(self, symbols: List[str]) -> AsyncIterator[MarketQuote]:
        if not self._is_connected:
            raise ConnectionError("DataAdapter not connected")

        logger.info(f"Started streaming mock quotes for: {symbols}")

        while self._is_connected:
            for sys in symbols:
                yield await self.get_quote(sys)

            # Simulate tick latency
            await asyncio.sleep(random.uniform(0.1, 0.5))

    @property
    def provider_name(self) -> str:
        return "DevMockFeed"

    @property
    def is_licensed(self) -> bool:
        return False
