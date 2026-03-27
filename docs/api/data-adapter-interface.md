# Data Adapter Interface

**Abstract adapter pattern for market data providers.**
**Version:** 0.1.0 | **Date:** 2026-03-26

---

## Overview

The platform uses an **Adapter Pattern** to abstract data provider implementations. This allows swapping between development (free) and production (licensed) data sources without code changes.

> ⚠️ **CRITICAL:** Free data sources (NSE scraping, Yahoo Finance) are for **development only**. Production **MUST** use licensed feeds (TrueData, GlobalDataFeeds).

---

## Interface Definition

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import AsyncIterator


class TimeFrame(Enum):
    TICK = "tick"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    DAY_1 = "1d"


@dataclass
class MarketQuote:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str  # Data provider attribution


@dataclass
class OrderBook:
    symbol: str
    timestamp: datetime
    bids: list[tuple[float, int]]  # (price, quantity)
    asks: list[tuple[float, int]]
    source: str


class DataAdapter(ABC):
    """Abstract base class for all market data adapters."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to data provider."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection gracefully."""
        ...

    @abstractmethod
    async def get_quote(self, symbol: str) -> MarketQuote:
        """Get latest quote for a symbol."""
        ...

    @abstractmethod
    async def get_historical(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start: datetime,
        end: datetime,
    ) -> list[MarketQuote]:
        """Get historical OHLCV data."""
        ...

    @abstractmethod
    async def stream_quotes(
        self, symbols: list[str]
    ) -> AsyncIterator[MarketQuote]:
        """Stream real-time quotes for symbols."""
        ...

    @abstractmethod
    async def get_order_book(self, symbol: str) -> OrderBook:
        """Get current order book snapshot."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the data provider for attribution."""
        ...

    @property
    @abstractmethod
    def is_licensed(self) -> bool:
        """Whether this is a licensed (production-ready) provider."""
        ...
```

---

## Provider Implementations (Planned)

| Provider | Type | Phase | Status |
|----------|------|-------|--------|
| `DevDataAdapter` | Development (mock/free) | Phase 0 | 🔲 Planned |
| `TrueDataAdapter` | Licensed (production) | Phase 1 | 🔲 Planned |
| `GlobalDataFeedsAdapter` | Licensed (production) | Phase 1 | 🔲 Planned |

---

## Usage Pattern

```python
from data.adapters import TrueDataAdapter, DevDataAdapter

# Development
adapter = DevDataAdapter()

# Production
adapter = TrueDataAdapter(api_key=settings.truedata_api_key)

# Same interface regardless of provider
await adapter.connect()
quote = await adapter.get_quote("RELIANCE")
print(f"₹{quote.close} via {quote.source}")
await adapter.disconnect()
```

---

## Configuration

Data provider selection is driven by environment:

```python
def get_data_adapter() -> DataAdapter:
    if settings.app_env == "production":
        return TrueDataAdapter(api_key=settings.truedata_api_key)
    return DevDataAdapter()
```

This ensures **no free/scraped data** reaches production systems.
