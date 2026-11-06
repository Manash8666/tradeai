"""
Institutional Indian Paper Trading API Router
=============================================
Exposes REST endpoints powering the frontend Live Trading Desk and Strategy Builder:
- Order Placement with realistic execution and slippage
- Account Balances, Tiered Risk State & Double-Entry Ledger
- Positions & Position Square-Off
- Pre-Trade Risk Guard (2% Gap-down simulation, Capital-at-risk %)
- Contextual Event-Driven Tagging & Sentiment Impact Meter
- Indian Statutory Tax Engine (STT, NSE, SEBI, Stamp, GST)
- SEBI Multi-Leg SPAN Margin Netting & Portfolio Greeks
- 3D SABR Calibrated Volatility Surface
- Automated Post-Trade Analytics & Behavioral Metrics
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.trading.contextual_news_engine import contextual_news_engine
from backend.app.trading.institutional_paper_engine import (
    institutional_paper_engine,
    OrderSide,
    OrderStatus,
    OrderType,
)
from backend.app.trading.options_risk import (
    BlackScholesGreeksEngine,
    OptionLeg,
    OptionType as OptType,
    SEBIMarginNettingEngine,
)
from backend.app.trading.sabr_calibrator import sabr_calibrator
from backend.app.trading.tax_engine import IndianTaxEngine, Segment

router = APIRouter(prefix="/api/paper", tags=["Institutional Paper Trading"])


# ── Request / Response Models ──

class PaperOrderRequest(BaseModel):
    symbol: str
    side: str = Field(pattern="^(BUY|SELL|buy|sell)$")
    type: str = Field(default="MARKET", pattern="^(MARKET|LIMIT|SL|SL_M|SL-M|market|limit|sl|sl_m|sl-m)$")
    quantity: int = Field(gt=0)
    price: float = Field(default=0.0)
    trigger_price: float = Field(default=0.0)
    sl_points: float = Field(default=20.0)
    target_points: float = Field(default=40.0)
    segment: str = Field(default="EQUITY_INTRADAY")


class PreTradeRiskRequest(BaseModel):
    symbol: str
    side: str = Field(pattern="^(BUY|SELL|buy|sell)$")
    quantity: int = Field(gt=0)
    price: float = Field(gt=0.0)
    sl_points: float = Field(default=20.0)
    segment: str = Field(default="EQUITY_INTRADAY")


class ClosePositionRequest(BaseModel):
    symbol: str


class OptionLegModel(BaseModel):
    strike: float
    option_type: str = Field(pattern="^(CE|PE|call|put)$")
    action: str = Field(pattern="^(BUY|SELL|buy|sell)$")
    quantity: int = Field(gt=0)
    price: float = Field(gt=0.0)
    iv: float = Field(default=0.14)
    days_to_expiry: float = Field(default=7.0)


class MarginNettingRequest(BaseModel):
    spot: float
    legs: List[OptionLegModel]


# ── Endpoints ──

@router.get("/account")
async def get_account_summary():
    """Retrieve virtual cash, portfolio equity, double-entry audit, and risk state."""
    return institutional_paper_engine.get_account_summary()


@router.get("/positions")
async def get_positions():
    """Retrieve all open positions with live unrealized P&L and holding durations."""
    return [pos.to_dict() for pos in institutional_paper_engine.positions.values()]


@router.get("/trades")
async def get_completed_trades():
    """Retrieve completed round-trip trades with post-mortems and behavioral analytics."""
    return {
        "trades": [t.to_dict() for t in institutional_paper_engine.completed_trades],
        "analytics": institutional_paper_engine.compute_behavioral_analytics(),
    }


@router.post("/order")
async def place_paper_order(req: PaperOrderRequest):
    """Place a simulated order with pre-trade risk check, slippage, and statutory tax accounting."""
    side_enum = OrderSide.BUY if req.side.upper() == "BUY" else OrderSide.SELL

    order_type_str = req.type.upper().replace("-", "_")
    if order_type_str == "MARKET":
        type_enum = OrderType.MARKET
    elif order_type_str == "LIMIT":
        type_enum = OrderType.LIMIT
    elif order_type_str == "SL":
        type_enum = OrderType.SL
    else:
        type_enum = OrderType.SL_M

    try:
        segment_enum = Segment(req.segment.upper())
    except ValueError:
        segment_enum = Segment.EQUITY_INTRADAY

    result = institutional_paper_engine.place_order(
        symbol=req.symbol.upper(),
        side=side_enum,
        order_type=type_enum,
        quantity=req.quantity,
        limit_price=req.price,
        trigger_price=req.trigger_price,
        sl_points=req.sl_points,
        target_points=req.target_points,
        segment=segment_enum,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Order placement failed"))

    return result


@router.post("/close_position")
async def close_position(req: ClosePositionRequest):
    """Close an open position at current market price."""
    res = institutional_paper_engine.close_position(req.symbol.upper())
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to close position"))
    return res


@router.post("/pre_trade_risk")
async def pre_trade_risk_check(req: PreTradeRiskRequest):
    """Simulate pre-trade risk before order ticket dispatch."""
    side_enum = OrderSide.BUY if req.side.upper() == "BUY" else OrderSide.SELL
    try:
        segment_enum = Segment(req.segment.upper())
    except ValueError:
        segment_enum = Segment.EQUITY_INTRADAY

    return institutional_paper_engine.simulate_pre_trade_risk(
        symbol=req.symbol.upper(),
        side=side_enum,
        quantity=req.quantity,
        price=req.price,
        sl_points=req.sl_points,
        segment=segment_enum,
    )


@router.get("/tax_calculator")
async def calculate_statutory_taxes(
    buy_price: float = Query(gt=0),
    sell_price: float = Query(gt=0),
    quantity: int = Query(gt=0),
    segment: str = Query(default="EQUITY_INTRADAY"),
):
    """Calculate exact statutory tax breakdown (STT, NSE, SEBI, Stamp, GST) for a trade."""
    try:
        segment_enum = Segment(segment.upper())
    except ValueError:
        segment_enum = Segment.EQUITY_INTRADAY

    res = IndianTaxEngine.calculate_round_trip(
        buy_price=buy_price,
        sell_price=sell_price,
        quantity=quantity,
        segment=segment_enum,
    )
    return res.to_dict()


@router.get("/contextual_news")
async def get_contextual_news():
    """Retrieve macroeconomic catalysts with affected sectors and symbol mappings."""
    return contextual_news_engine.get_all_events()


@router.get("/contextual_news/{symbol}")
async def get_symbol_contextual_sentiment(symbol: str):
    """Retrieve symbol-specific sentiment impact score and active catalyst tags."""
    return contextual_news_engine.get_symbol_context(symbol)


@router.post("/options_margin")
async def calculate_options_margin_netting(req: MarginNettingRequest):
    """Calculate SEBI SPAN multi-leg margin netting relief and portfolio Greeks."""
    legs = []
    for l in req.legs:
        opt_type = OptType.CALL if l.option_type.upper() in ("CE", "CALL") else OptType.PUT
        legs.append(
            OptionLeg(
                strike=l.strike,
                option_type=opt_type,
                action=l.action.upper(),
                quantity=l.quantity,
                price=l.price,
                iv=l.iv,
                days_to_expiry=l.days_to_expiry,
            )
        )

    margin_analysis = SEBIMarginNettingEngine.calculate_margin(req.spot, legs)
    portfolio_greeks = BlackScholesGreeksEngine.aggregate_portfolio_greeks(req.spot, legs)

    return {
        "margin_netting": margin_analysis,
        "portfolio_greeks": portfolio_greeks.to_dict(),
    }


@router.get("/sabr_surface")
async def get_sabr_volatility_surface(
    forward: float = Query(default=23800.0),
    base_iv: float = Query(default=0.138),
):
    """Retrieve 3D SABR calibrated volatility surface grid (Strike x DTE x Volatility)."""
    return sabr_calibrator.generate_3d_surface(forward=forward, base_iv=base_iv)


@router.post("/reset_account")
async def reset_paper_account(initial_capital: float = Query(default=1_000_000.0)):
    """Reset virtual account balances, positions, and circuit breakers."""
    institutional_paper_engine.__init__(initial_capital=initial_capital)
    return {
        "success": True,
        "message": f"Account reset to ₹{initial_capital:,.2f}. Balance conserved.",
        "account": institutional_paper_engine.get_account_summary(),
    }
