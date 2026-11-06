"""
Institutional Indian Statutory Tax & Transaction Cost Engine
============================================================
Accurate replication of the complete Indian regulatory fee schedule
mandated by SEBI, NSE/BSE, and the Ministry of Finance.

Segments Supported:
- EQUITY_INTRADAY (MIS)
- EQUITY_DELIVERY (CNC)
- EQUITY_FUTURES (NIFTY/BANKNIFTY/Stock Futures)
- EQUITY_OPTIONS (Index & Stock Option Premiums)
- COMMODITY_FUTURES (MCX Crude, Gold, Silver)

Charges Simulated:
1. Brokerage (Discount broker standard: min(Rs 20, 0.03% turnover))
2. STT / CTT (Securities / Commodity Transaction Tax)
3. Exchange Transaction Charges (NSE / MCX)
4. SEBI Turnover Charges (Rs 10 per Crore)
5. Stamp Duty (State / Revenue stamp duty on buy side)
6. GST (18% on Brokerage + Exchange Txn + SEBI Charges)
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any


class Segment(str, Enum):
    EQUITY_INTRADAY = "EQUITY_INTRADAY"
    EQUITY_DELIVERY = "EQUITY_DELIVERY"
    EQUITY_FUTURES = "EQUITY_FUTURES"
    EQUITY_OPTIONS = "EQUITY_OPTIONS"
    COMMODITY_FUTURES = "COMMODITY_FUTURES"


@dataclass
class StatutoryCostBreakdown:
    turnover: float
    brokerage: float
    stt_ctt: float
    exchange_txn_fee: float
    sebi_turnover_fee: float
    stamp_duty: float
    gst: float
    total_tax_and_charges: float
    breakeven_points: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turnover": round(self.turnover, 2),
            "brokerage": round(self.brokerage, 2),
            "stt_ctt": round(self.stt_ctt, 2),
            "exchange_txn_fee": round(self.exchange_txn_fee, 2),
            "sebi_turnover_fee": round(self.sebi_turnover_fee, 2),
            "stamp_duty": round(self.stamp_duty, 2),
            "gst": round(self.gst, 2),
            "total_tax_and_charges": round(self.total_tax_and_charges, 2),
            "breakeven_points": round(self.breakeven_points, 4),
        }


@dataclass
class RoundTripTradeResult:
    buy_price: float
    sell_price: float
    quantity: int
    gross_pnl: float
    net_pnl: float
    cost_breakdown: StatutoryCostBreakdown

    def to_dict(self) -> Dict[str, Any]:
        return {
            "buy_price": round(self.buy_price, 2),
            "sell_price": round(self.sell_price, 2),
            "quantity": self.quantity,
            "gross_pnl": round(self.gross_pnl, 2),
            "net_pnl": round(self.net_pnl, 2),
            "cost_breakdown": self.cost_breakdown.to_dict(),
        }


class IndianTaxEngine:
    """Exact calculation engine for Indian market transaction costs."""

    # GST is standard 18% on (Brokerage + Exchange + SEBI)
    GST_RATE: float = 0.18

    # SEBI turnover charge: Rs 10 per Crore (0.0001%)
    SEBI_RATE: float = 0.000001

    @classmethod
    def calculate_single_leg(
        cls,
        side: str,  # 'BUY' or 'SELL'
        price: float,
        quantity: int,
        segment: Segment = Segment.EQUITY_INTRADAY,
    ) -> StatutoryCostBreakdown:
        """Calculate statutory costs for a single buy or sell order leg."""
        side = side.upper()
        turnover = price * quantity

        # 1. Brokerage
        if segment in (Segment.EQUITY_FUTURES, Segment.EQUITY_OPTIONS):
            brokerage = 20.0
        elif segment == Segment.EQUITY_DELIVERY:
            brokerage = 0.0
        else:
            brokerage = min(20.0, turnover * 0.0003)

        # 2. STT / CTT
        stt = 0.0
        if segment == Segment.EQUITY_INTRADAY and side == "SELL":
            stt = turnover * 0.00025  # 0.025% on sell
        elif segment == Segment.EQUITY_DELIVERY:
            stt = turnover * 0.001  # 0.1% on buy & sell
        elif segment == Segment.EQUITY_FUTURES and side == "SELL":
            stt = turnover * 0.0002  # 0.02% on sell (Budget 2024 rate)
        elif segment == Segment.EQUITY_OPTIONS and side == "SELL":
            stt = turnover * 0.001  # 0.1% on option sell premium
        elif segment == Segment.COMMODITY_FUTURES and side == "SELL":
            stt = turnover * 0.0001  # 0.01% CTT on sell

        # 3. Exchange Transaction Charges
        if segment in (Segment.EQUITY_INTRADAY, Segment.EQUITY_DELIVERY):
            exchange_fee = turnover * 0.0000297  # NSE 0.00297%
        elif segment == Segment.EQUITY_FUTURES:
            exchange_fee = turnover * 0.0000173  # NSE Futures 0.00173%
        elif segment == Segment.EQUITY_OPTIONS:
            exchange_fee = turnover * 0.0003503  # NSE Options 0.03503% on premium
        elif segment == Segment.COMMODITY_FUTURES:
            exchange_fee = turnover * 0.000021  # MCX 0.0021%
        else:
            exchange_fee = turnover * 0.0000297

        # 4. SEBI Turnover Fee
        sebi_fee = turnover * cls.SEBI_RATE

        # 5. Stamp Duty (Buy side only)
        stamp_duty = 0.0
        if side == "BUY":
            if segment == Segment.EQUITY_INTRADAY:
                stamp_duty = turnover * 0.00003  # 0.003%
            elif segment == Segment.EQUITY_DELIVERY:
                stamp_duty = turnover * 0.00015  # 0.015%
            elif segment in (Segment.EQUITY_FUTURES, Segment.COMMODITY_FUTURES):
                stamp_duty = turnover * 0.00002  # 0.002%
            elif segment == Segment.EQUITY_OPTIONS:
                stamp_duty = turnover * 0.00003  # 0.003%

        # 6. GST (18% on Brokerage + Exchange + SEBI)
        gst = (brokerage + exchange_fee + sebi_fee) * cls.GST_RATE

        total = brokerage + stt + exchange_fee + sebi_fee + stamp_duty + gst
        breakeven = total / quantity if quantity > 0 else 0.0

        return StatutoryCostBreakdown(
            turnover=turnover,
            brokerage=brokerage,
            stt_ctt=stt,
            exchange_txn_fee=exchange_fee,
            sebi_turnover_fee=sebi_fee,
            stamp_duty=stamp_duty,
            gst=gst,
            total_tax_and_charges=total,
            breakeven_points=breakeven,
        )

    @classmethod
    def calculate_round_trip(
        cls,
        buy_price: float,
        sell_price: float,
        quantity: int,
        segment: Segment = Segment.EQUITY_INTRADAY,
    ) -> RoundTripTradeResult:
        """Calculate complete round-trip (entry and exit) statutory costs and Net P&L."""
        buy_leg = cls.calculate_single_leg("BUY", buy_price, quantity, segment)
        sell_leg = cls.calculate_single_leg("SELL", sell_price, quantity, segment)

        total_turnover = buy_leg.turnover + sell_leg.turnover
        total_brokerage = buy_leg.brokerage + sell_leg.brokerage
        total_stt = buy_leg.stt_ctt + sell_leg.stt_ctt
        total_exchange = buy_leg.exchange_txn_fee + sell_leg.exchange_txn_fee
        total_sebi = buy_leg.sebi_turnover_fee + sell_leg.sebi_turnover_fee
        total_stamp = buy_leg.stamp_duty + sell_leg.stamp_duty
        total_gst = buy_leg.gst + sell_leg.gst
        total_charges = buy_leg.total_tax_and_charges + sell_leg.total_tax_and_charges

        breakeven = total_charges / quantity if quantity > 0 else 0.0
        gross_pnl = (sell_price - buy_price) * quantity
        net_pnl = gross_pnl - total_charges

        cost_breakdown = StatutoryCostBreakdown(
            turnover=total_turnover,
            brokerage=total_brokerage,
            stt_ctt=total_stt,
            exchange_txn_fee=total_exchange,
            sebi_turnover_fee=total_sebi,
            stamp_duty=total_stamp,
            gst=total_gst,
            total_tax_and_charges=total_charges,
            breakeven_points=breakeven,
        )

        return RoundTripTradeResult(
            buy_price=buy_price,
            sell_price=sell_price,
            quantity=quantity,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            cost_breakdown=cost_breakdown,
        )
