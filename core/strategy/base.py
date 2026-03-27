"""
Base Strategy Interface

Standardizes the hook mappings between NautilusTrader's event loops
and our internal Trading strategies.
"""

from abc import abstractmethod

from nautilus_trader.model.data.quote import QuoteTick
from nautilus_trader.trading.strategy import Strategy


class BaseStrategy(Strategy):
    """Core Strategy extension mapping to standard conventions."""

    def __init__(self, config) -> None:
        super().__init__(config)

    def on_start(self) -> None:
        """Called when strategy starts."""
        self.log.info(f"Strategy {self.__class__.__name__} started.")

    def on_stop(self) -> None:
        """Called when strategy is stopped."""
        self.log.info(f"Strategy {self.__class__.__name__} stopped.")

    @abstractmethod
    def on_quote_tick(self, tick: QuoteTick) -> None:
        """Process incoming market ticks."""
        pass
