"""
Trading Engine API Router

Endpoints to control the underlying NautilusTrader Engine and view its status.
Wrapped with our Auth & Audit logging middleware.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.auth.dependencies import get_current_user
from backend.app.models.user import User
from core.engine import engine_wrapper
from core.paper_trader import PaperBroker

paper_broker = PaperBroker()

router = APIRouter(
    prefix="/trading",
    tags=["Trading Engine"],
    dependencies=[Depends(get_current_user)],  # All endpoints require auth
)


class EngineStatusResponse(BaseModel):
    is_running: bool
    status: str


@router.post("/start", response_model=EngineStatusResponse)
async def start_engine(current_user: User = Depends(get_current_user)):
    """Initialize and start the Core Trading Engine."""
    if engine_wrapper.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NautilusTrader Engine is already running.",
        )

    try:
        await engine_wrapper.start()
        return {"is_running": True, "status": "Engine started successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Engine failed to start: {str(e)}",
        )


@router.post("/stop", response_model=EngineStatusResponse)
async def stop_engine(current_user: User = Depends(get_current_user)):
    """Stop the Core Trading Engine gracefully."""
    if not engine_wrapper.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NautilusTrader Engine is not currently running.",
        )

    try:
        await engine_wrapper.stop()
        return {"is_running": False, "status": "Engine stopped successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Engine failed to stop: {str(e)}",
        )


@router.get("/status", response_model=EngineStatusResponse)
async def get_engine_status(current_user: User = Depends(get_current_user)):
    """Get the current running status of the Trading Engine."""
    return {
        "is_running": engine_wrapper.is_running,
        "status": "Running" if engine_wrapper.is_running else "Stopped",
    }


class PaperOrderRequest(BaseModel):
    symbol: str
    qty: int = Field(gt=0)
    side: str = Field(pattern="^(BUY|SELL)$")
    order_type: str = Field(default="MARKET", pattern="^(MARKET|LIMIT)$")
    price: float = 0.0
    algo_id: str | None = None


@router.post("/paper/order")
async def place_paper_order(
    order: PaperOrderRequest, current_user: User = Depends(get_current_user)
):
    """Place a synthetic paper trade against the Mock Broker."""
    if not paper_broker.is_connected:
        await paper_broker.connect()

    try:
        res = await paper_broker.place_order(
            symbol=order.symbol,
            qty=order.qty,
            side=order.side,
            order_type=order.order_type,
            price=order.price,
            algo_id=order.algo_id,
        )
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Paper order failed: {str(e)}",
        )


@router.get("/paper/positions")
async def get_paper_positions(current_user: User = Depends(get_current_user)):
    """Retrieve simulated open positions from the Mock Broker."""
    return await paper_broker.get_positions()
