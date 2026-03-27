"""
Backtesting API Router

Allows the frontend dashboard to trigger historical strategy simulations
and retrieve performance metrics.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.app.auth.dependencies import get_current_active_user
from backend.app.models.user import User

from tests.backtest.engine import StrategyBacktester

router = APIRouter(
    prefix="/backtest",
    tags=["Strategy Backtesting"],
    dependencies=[Depends(get_current_active_user)],
)

backtester = StrategyBacktester()


class BacktestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    model_id: str = "baseline_v1"


@router.post("/run")
async def run_backtest_simulation(
    req: BacktestRequest, current_user: User = Depends(get_current_active_user)
):
    """
    Trigger a historical backtest execution via NautilusTrader.
    Currently heavily mocked for Phase 2 validation, returns dummy equity curves.
    """
    return backtester.run_backtest(
        symbol=req.symbol, start_date=req.start_date, end_date=req.end_date
    )
