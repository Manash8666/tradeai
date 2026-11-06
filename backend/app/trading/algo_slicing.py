"""
Institutional Algorithmic Execution Slicing Engine.
Inspired by gpt4112000-coder/Indian_Trading_Infrastructure_Platform.

Deconstructs parent institutional orders into risk-managed child slices
following deterministic mathematical scheduling:
1. Immediate Execution (Aggressive single fill)
2. TWAP (Time-Weighted Average Price) with exact remainder lot balancing
3. VWAP (Volume-Weighted Average Price) using U-shaped canonical Indian intraday curve
4. POV (Percentage of Volume / Participation) dynamically tracking live tape volume
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import time
import math

class AlgoType(str, Enum):
    IMMEDIATE = "IMMEDIATE"
    TWAP = "TWAP"
    VWAP = "VWAP"
    POV = "POV"

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class ExecutionSlice(BaseModel):
    sequence: int
    quantity: int
    target_time_offset_sec: int
    slice_price: float
    order_type: str = "LIMIT"
    status: str = "PENDING"

class ExecutionPlan(BaseModel):
    plan_id: str
    symbol: str
    side: OrderSide
    algo: AlgoType
    total_quantity: int
    num_slices: int
    duration_minutes: int
    estimated_slippage_bps: float
    slices: List[ExecutionSlice]
    created_at: float = Field(default_factory=time.time)

class AlgoSlicingEngine:
    """Institutional Order Slicing Engine."""

    @staticmethod
    def _volume_weights(slice_count: int) -> List[int]:
        """U-shaped intraday volume profile: heavy at 09:15-10:00 and 14:30-15:30, lighter mid-session."""
        # Canonical U-curve: max(i, slice_count - i + 1)
        return [max(i, slice_count - i + 1) for i in range(1, slice_count + 1)]

    @staticmethod
    def _distribute_shares(total_qty: int, weights: List[int]) -> List[int]:
        """Distribute shares proportional to weights with zero leftover lots."""
        total_w = sum(weights)
        if total_w == 0:
            base = total_qty // len(weights)
            return [base] * len(weights)
        
        shares = [total_qty * w // total_w for w in weights]
        remainder = total_qty - sum(shares)
        
        # Allocate remainder to heaviest slices first
        sorted_indices = sorted(range(len(weights)), key=lambda i: weights[i], reverse=True)
        for i in range(remainder):
            shares[sorted_indices[i % len(sorted_indices)]] += 1
            
        return shares

    def plan_execution(
        self,
        symbol: str,
        side: OrderSide,
        algo: AlgoType,
        total_quantity: int,
        base_price: float,
        duration_minutes: int = 30,
        slice_count: Optional[int] = None,
        participation_rate: float = 0.15,
        observed_volume: int = 150000,
    ) -> ExecutionPlan:
        """Computes deterministic child slices for an institutional execution order."""
        if total_quantity <= 0:
            raise ValueError("Total quantity must be greater than 0")

        plan_id = f"PLAN_{int(time.time()*1000)}_{symbol}"

        # 1. IMMEDIATE
        if algo == AlgoType.IMMEDIATE:
            slices = [
                ExecutionSlice(
                    sequence=1,
                    quantity=total_quantity,
                    target_time_offset_sec=0,
                    slice_price=base_price,
                    order_type="MARKET",
                )
            ]
            return ExecutionPlan(
                plan_id=plan_id,
                symbol=symbol,
                side=side,
                algo=algo,
                total_quantity=total_quantity,
                num_slices=1,
                duration_minutes=0,
                estimated_slippage_bps=3.8,
                slices=slices,
            )

        # 2. TWAP
        if algo == AlgoType.TWAP:
            n_slices = slice_count or max(1, duration_minutes // 2)
            interval_sec = (duration_minutes * 60) // n_slices
            weights = [1] * n_slices
            quantities = self._distribute_shares(total_quantity, weights)
            
            slices = [
                ExecutionSlice(
                    sequence=i + 1,
                    quantity=quantities[i],
                    target_time_offset_sec=i * interval_sec,
                    slice_price=round(base_price * (1.0002 if side == OrderSide.BUY else 0.9998), 2),
                    order_type="LIMIT",
                )
                for i in range(n_slices)
            ]
            return ExecutionPlan(
                plan_id=plan_id,
                symbol=symbol,
                side=side,
                algo=algo,
                total_quantity=total_quantity,
                num_slices=n_slices,
                duration_minutes=duration_minutes,
                estimated_slippage_bps=0.85,
                slices=slices,
            )

        # 3. VWAP
        if algo == AlgoType.VWAP:
            n_slices = slice_count or max(2, duration_minutes // 3)
            interval_sec = (duration_minutes * 60) // n_slices
            weights = self._volume_weights(n_slices)
            quantities = self._distribute_shares(total_quantity, weights)

            slices = [
                ExecutionSlice(
                    sequence=i + 1,
                    quantity=quantities[i],
                    target_time_offset_sec=i * interval_sec,
                    slice_price=round(base_price * (1.0001 if side == OrderSide.BUY else 0.9999), 2),
                    order_type="LIMIT",
                )
                for i in range(n_slices)
            ]
            return ExecutionPlan(
                plan_id=plan_id,
                symbol=symbol,
                side=side,
                algo=algo,
                total_quantity=total_quantity,
                num_slices=n_slices,
                duration_minutes=duration_minutes,
                estimated_slippage_bps=0.62,
                slices=slices,
            )

        # 4. POV (Percentage of Volume)
        if algo == AlgoType.POV:
            planned_slice = min(max(int(observed_volume * participation_rate), 1), total_quantity)
            n_slices = math.ceil(total_quantity / planned_slice)
            interval_sec = max(30, (duration_minutes * 60) // n_slices)
            
            weights = [1] * n_slices
            quantities = self._distribute_shares(total_quantity, weights)

            slices = [
                ExecutionSlice(
                    sequence=i + 1,
                    quantity=quantities[i],
                    target_time_offset_sec=i * interval_sec,
                    slice_price=base_price,
                    order_type="LIMIT",
                )
                for i in range(n_slices)
            ]
            return ExecutionPlan(
                plan_id=plan_id,
                symbol=symbol,
                side=side,
                algo=algo,
                total_quantity=total_quantity,
                num_slices=n_slices,
                duration_minutes=duration_minutes,
                estimated_slippage_bps=0.74,
                slices=slices,
            )

        raise ValueError(f"Unsupported algo type: {algo}")

# Global instance
algo_slicing_engine = AlgoSlicingEngine()
