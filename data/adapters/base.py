"""
Base Data Adapter Interface

Defines the core interface for fetching historical and streaming real-time
market tick data. Used to enforce consistent data structures across various
upstream providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import AsyncIterator, List


class TimeFrame(Enum):
    TICK = "tick"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    DAY_1 = "1d"


@dataclass
class MarketQuote:
    """Standardized OHLCV + Tick Quote model."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str  # Data provider attribution


class DataAdapter(ABC):
    """Abstract base class for all market data adapters."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to data provider."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection gracefully."""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> MarketQuote:
        """Get latest snapshot quote for a symbol."""
        pass

    @abstractmethod
    async def stream_quotes(self, symbols: List[str]) -> AsyncIterator[MarketQuote]:
        """Stream real-time quotes/ticks for symbols via WebSocket."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the data provider for attribution."""
        pass

    @property
    @abstractmethod
    def is_licensed(self) -> bool:
        """Whether this is a licensed (production-ready) provider."""
        pass
