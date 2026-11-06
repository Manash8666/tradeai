"""
High-Performance In-Memory Limit Order Book & Event Matcher
===========================================================
Implements discrete event matching using heapq priority queues:
- BUY Orders: Max-heap (highest price priority, FIFO on tie)
- SELL Orders: Min-heap (lowest price priority, FIFO on tie)
- Stop-Loss (SL / SL-M): Trigger queue evaluated on every market tick
- Market Impact Slippage: Almgren-Chriss square-root depth exhaustion model
"""

import heapq
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"          # Stop-Loss Limit (requires trigger_price + limit_price)
    SL_M = "SL_M"      # Stop-Loss Market (requires trigger_price)


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    TRIGGER_PENDING = "TRIGGER_PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class PaperOrder:
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    filled_qty: int = 0
    limit_price: float = 0.0
    trigger_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: float = field(default_factory=time.time)
    filled_at: Optional[float] = None
    average_fill_price: float = 0.0
    slippage_paid: float = 0.0
    sl_points: float = 0.0
    target_points: float = 0.0
    client_id: str = "DEFAULT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "filled_qty": self.filled_qty,
            "limit_price": round(self.limit_price, 2),
            "trigger_price": round(self.trigger_price, 2),
            "status": self.status.value,
            "created_at": self.created_at,
            "filled_at": self.filled_at,
            "average_fill_price": round(self.average_fill_price, 2),
            "slippage_paid": round(self.slippage_paid, 2),
            "sl_points": self.sl_points,
            "target_points": self.target_points,
        }


@dataclass
class FillEvent:
    fill_id: str
    order_id: str
    symbol: str
    side: OrderSide
    filled_qty: int
    fill_price: float
    slippage: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fill_id": self.fill_id,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "filled_qty": self.filled_qty,
            "fill_price": round(self.fill_price, 2),
            "slippage": round(self.slippage, 4),
            "timestamp": self.timestamp,
        }


class InstrumentOrderBook:
    """In-memory discrete matching book for a single instrument."""

    def __init__(self, symbol: str, tick_size: float = 0.05):
        self.symbol = symbol
        self.tick_size = tick_size

        # heapq buy orders: entries are (-limit_price, timestamp, order_id, order)
        self._buy_heap: List[Tuple[float, float, str, PaperOrder]] = []

        # heapq sell orders: entries are (limit_price, timestamp, order_id, order)
        self._sell_heap: List[Tuple[float, float, str, PaperOrder]] = []

        # Trigger orders (SL and SL-M) waiting for tick price activation
        self._trigger_orders: Dict[str, PaperOrder] = {}

        # All orders indexed by id
        self.all_orders: Dict[str, PaperOrder] = {}

        # Latest market reference price
        self.ltp: float = 0.0
        self.last_bid: float = 0.0
        self.last_ask: float = 0.0

    def compute_slippage(
        self,
        order_qty: int,
        base_price: float,
        depth_qty: int = 5000,
        eta: float = 0.02,
        volatility: float = 0.15,
    ) -> float:
        """
        Almgren-Chriss square-root law for realistic liquidity impact slippage:
        Slippage = eta * vol * sqrt(order_qty / depth) + (spread / 2)
        """
        spread = max(self.tick_size, base_price * 0.0002)
        impact = eta * (base_price * volatility * 0.01) * math.sqrt(max(1, order_qty) / max(100, depth_qty))
        return round(spread * 0.5 + impact, 2)

    def place_order(self, order: PaperOrder, current_market_price: Optional[float] = None) -> List[FillEvent]:
        """Submit a new paper order into the matching engine."""
        if current_market_price and current_market_price > 0:
            self.ltp = current_market_price

        self.all_orders[order.order_id] = order
        fills: List[FillEvent] = []

        # 1. Check if Stop Loss Trigger Order
        if order.order_type in (OrderType.SL, OrderType.SL_M):
            order.status = OrderStatus.TRIGGER_PENDING
            self._trigger_orders[order.order_id] = order
            # Evaluate immediately against current LTP
            if self.ltp > 0:
                fills.extend(self.process_tick(self.ltp))
            return fills

        # 2. Market Order (Immediate Fill with Slippage)
        if order.order_type == OrderType.MARKET:
            fills.append(self._execute_market_fill(order))
            return fills

        # 3. Limit Order
        if order.order_type == OrderType.LIMIT:
            # Check if limit crosses current market price immediately
            if self.ltp > 0:
                if order.side == OrderSide.BUY and order.limit_price >= self.ltp:
                    fills.append(self._execute_market_fill(order, forced_price=min(order.limit_price, self.ltp)))
                    return fills
                elif order.side == OrderSide.SELL and order.limit_price <= self.ltp:
                    fills.append(self._execute_market_fill(order, forced_price=max(order.limit_price, self.ltp)))
                    return fills

            # Insert into priority queue
            if order.side == OrderSide.BUY:
                heapq.heappush(self._buy_heap, (-order.limit_price, order.created_at, order.order_id, order))
            else:
                heapq.heappush(self._sell_heap, (order.limit_price, order.created_at, order.order_id, order))
            order.status = OrderStatus.PENDING

        return fills

    def _execute_market_fill(self, order: PaperOrder, forced_price: Optional[float] = None) -> FillEvent:
        """Execute a market fill with realistic spread and impact slippage."""
        base_price = forced_price if forced_price else (self.ltp if self.ltp > 0 else order.limit_price)
        slippage = self.compute_slippage(order.quantity, base_price)

        if order.side == OrderSide.BUY:
            fill_price = base_price + slippage
        else:
            fill_price = max(self.tick_size, base_price - slippage)

        order.filled_qty = order.quantity
        order.status = OrderStatus.FILLED
        order.filled_at = time.time()
        order.average_fill_price = fill_price
        order.slippage_paid = slippage

        return FillEvent(
            fill_id=f"FILL_{uuid4().hex[:8].upper()}",
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            filled_qty=order.quantity,
            fill_price=fill_price,
            slippage=slippage,
            timestamp=order.filled_at,
        )

    def process_tick(self, ltp: float, high: Optional[float] = None, low: Optional[float] = None) -> List[FillEvent]:
        """
        Evaluate order book against an incoming market tick:
        1. Checks trigger orders (SL / SL-M).
        2. Matches limit buy orders if ltp <= limit_price.
        3. Matches limit sell orders if ltp >= limit_price.
        """
        self.ltp = ltp
        high_price = high if high is not None else ltp
        low_price = low if low is not None else ltp

        fills: List[FillEvent] = []

        # ── STEP A: TRIGGER SL / SL-M ORDERS ──
        triggered_ids = []
        for order_id, order in list(self._trigger_orders.items()):
            is_triggered = False
            # Buy SL triggers if market rises to or above trigger
            if order.side == OrderSide.BUY and high_price >= order.trigger_price:
                is_triggered = True
            # Sell SL triggers if market falls to or below trigger
            elif order.side == OrderSide.SELL and low_price <= order.trigger_price:
                is_triggered = True

            if is_triggered:
                triggered_ids.append(order_id)
                if order.order_type == OrderType.SL_M:
                    fills.append(self._execute_market_fill(order))
                else:
                    # Promote SL to Limit
                    order.order_type = OrderType.LIMIT
                    if order.side == OrderSide.BUY:
                        heapq.heappush(self._buy_heap, (-order.limit_price, time.time(), order.order_id, order))
                    else:
                        heapq.heappush(self._sell_heap, (order.limit_price, time.time(), order.order_id, order))
                    order.status = OrderStatus.PENDING

        for tid in triggered_ids:
            self._trigger_orders.pop(tid, None)

        # ── STEP B: MATCH LIMIT BUYS ──
        while self._buy_heap:
            neg_price, ts, oid, order = self._buy_heap[0]
            limit_price = -neg_price
            if order.status == OrderStatus.CANCELLED:
                heapq.heappop(self._buy_heap)
                continue

            if low_price <= limit_price:
                heapq.heappop(self._buy_heap)
                # Filled at limit price or lower
                exec_price = min(limit_price, ltp)
                order.filled_qty = order.quantity
                order.status = OrderStatus.FILLED
                order.filled_at = time.time()
                order.average_fill_price = exec_price
                order.slippage_paid = 0.0

                fills.append(
                    FillEvent(
                        fill_id=f"FILL_{uuid4().hex[:8].upper()}",
                        order_id=order.order_id,
                        symbol=order.symbol,
                        side=order.side,
                        filled_qty=order.quantity,
                        fill_price=exec_price,
                        slippage=0.0,
                        timestamp=order.filled_at,
                    )
                )
            else:
                break

        # ── STEP C: MATCH LIMIT SELLS ──
        while self._sell_heap:
            limit_price, ts, oid, order = self._sell_heap[0]
            if order.status == OrderStatus.CANCELLED:
                heapq.heappop(self._sell_heap)
                continue

            if high_price >= limit_price:
                heapq.heappop(self._sell_heap)
                exec_price = max(limit_price, ltp)
                order.filled_qty = order.quantity
                order.status = OrderStatus.FILLED
                order.filled_at = time.time()
                order.average_fill_price = exec_price
                order.slippage_paid = 0.0

                fills.append(
                    FillEvent(
                        fill_id=f"FILL_{uuid4().hex[:8].upper()}",
                        order_id=order.order_id,
                        symbol=order.symbol,
                        side=order.side,
                        filled_qty=order.quantity,
                        fill_price=exec_price,
                        slippage=0.0,
                        timestamp=order.filled_at,
                    )
                )
            else:
                break

        return fills

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open limit or trigger order."""
        if order_id in self._trigger_orders:
            order = self._trigger_orders.pop(order_id)
            order.status = OrderStatus.CANCELLED
            return True

        if order_id in self.all_orders:
            order = self.all_orders[order_id]
            if order.status in (OrderStatus.PENDING, OrderStatus.TRIGGER_PENDING):
                order.status = OrderStatus.CANCELLED
                return True

        return False
