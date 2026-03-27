"""
Paper Trading Mock Broker

A synthetic broker that executes trades internally against the DevDataAdapter
stream for Risk-Free algorithmic strategy validation.
"""

import asyncio
import logging
from typing import Any, Dict
from uuid import uuid4

from brokers.base import BrokerAdapter
from core.message_bus import message_bus
from core.risk.engine import risk_manager

logger = logging.getLogger(__name__)


class PaperBroker(BrokerAdapter):
    """Executes paper trades by matching against the latest market prices instantly."""

    def __init__(self) -> None:
        self.is_connected = False
        self._positions: Dict[str, Dict[str, Any]] = {}

    async def connect(self) -> None:
        """Initialize mock connection natively."""
        self.is_connected = True
        logger.info("[MockBroker] Virtual trading connection established.")

    async def disconnect(self) -> None:
        """Tear down mock connection natively."""
        self.is_connected = False
        logger.info("[MockBroker] Virtual trading disconnected.")

    async def place_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str,
        price: float = 0.0,
        algo_id: str | None = None,
    ) -> Dict[str, Any]:
        """Process local order and publish filled status to the message bus immediately."""

        if not self.is_connected:
            raise ConnectionError("Make sure to connect() PaperBroker first.")

        order_id = f"MOCK_{uuid4().hex[:8].upper()}"
        assumed_price = price if price > 0 else 1000.0

        # Risk Management Pipeline Check
        current_pos = self._positions.get(symbol, {"qty": 0, "avg_price": 0.0})
        current_exposure = current_pos["qty"] * current_pos["avg_price"]

        risk_manager.validate_pre_trade(
            symbol=symbol,
            side=side,
            qty=qty,
            price=assumed_price,
            current_exposure=current_exposure,
        )

        logger.info(f"Paper Order Placed | {symbol} | {side} | QTY: {qty} | Algo: {algo_id}")

        # In a real environment, this might wait for the orderbook to cross
        # Here we instantly execute a "Fill" event
        fill_event = {
            "event": "order_filled",
            "order_id": order_id,
            "symbol": symbol,
            "qty": qty,
            "side": side.upper(),
            "price": assumed_price,
            "status": "COMPLETED",
            "algo_id": algo_id,
        }

        # Track internal position
        multiplier = 1 if side.upper() == "BUY" else -1
        if symbol not in self._positions:
            self._positions[symbol] = {"qty": 0, "avg_price": 0.0}

        current_pos = self._positions[symbol]
        total_cost = (current_pos["qty"] * current_pos["avg_price"]) + (
            qty * fill_event["price"]
        ) * multiplier
        new_qty = current_pos["qty"] + (qty * multiplier)

        if new_qty != 0:
            current_pos["avg_price"] = total_cost / new_qty
        else:
            current_pos["avg_price"] = 0.0

        current_pos["qty"] = new_qty

        # Async stream to the REST API / WSS
        await message_bus.publish("trading_events", fill_event)

        return {
            "status": "success",
            "order_id": order_id,
            "message": "Paper trade simulated successfully",
        }

    async def cancel_order(self, order_id: str) -> bool:
        logger.info(f"[MockBroker] Canceling paper order {order_id}")
        return True

    async def get_positions(self) -> list[Dict[str, Any]]:
        return [{"symbol": sym, **data} for sym, data in self._positions.items()]

    @property
    def broker_name(self) -> str:
        return "PaperBroker-Dev"
