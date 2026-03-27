"""
Broker Base Adapter Interface

Defines the abstract contract for all broker integrations (Angel One, Zerodha, etc).
Enforces SEBI compliance tracking natively.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BrokerAdapter(ABC):
    """Abstract base class for executing trades and fetching account details."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish authenticated connection matching SEBI static IP rules."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully disconnect."""
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str,
        price: float = 0.0,
        algo_id: str | None = None,
    ) -> Dict[str, Any]:
        """
        Place an order to the exchange.
        
        Args:
            algo_id: SEBI mandatory Algo ID for automated trades.
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        pass

    @abstractmethod
    async def get_positions(self) -> list[Dict[str, Any]]:
        """Fetch current open positions."""
        pass

    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Identify the broker (e.g., 'AngelOne')."""
        pass
