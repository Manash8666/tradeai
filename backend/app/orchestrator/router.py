"""
API Router — AI Portfolio Orchestrator
=======================================
Exposes `/orchestrator/run` to manually trigger the Multi-Agent 
Portfolio orchestration cycle.
"""

import logging
from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.auth.dependencies import get_current_user
from backend.app.models.user import User
from core.orchestrator.portfolio_manager import PortfolioManager
from core.orchestrator.engines.healer_engine import Position

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orchestrator", tags=["AI Portfolio Orchestrator"])

# Single global instance of the manager
_manager = PortfolioManager()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class PositionInput(BaseModel):
    ticker: str
    entry_price: float
    current_price: float
    sentiment_score: float = 0.0
    momentum_score: float = 0.0


class OrchestratorRequest(BaseModel):
    positions: List[PositionInput] = Field(..., description="Current live portfolio positions.")
    candidates: List[PositionInput] = Field(default_factory=list, description="Watchlist for potential rotation.")
    news_headlines: Dict[str, List[str]] = Field(default_factory=dict, description="Recent news headlines keyed by ticker.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/run",
    summary="Run AI Orchestration Cycle",
    description="Executes Sentiment, Causality, RL stop-loss, Healer rotation, and Risk Parity logic.",
    status_code=status.HTTP_200_OK,
)
async def run_orchestrator(
    payload: OrchestratorRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """JWT-gated orchestration endpoint."""
    logger.info("Orchestrator run requested by %s", current_user.email)

    try:
        # Convert Pydantic inputs to internal dataclasses
        internal_positions = [
            Position(
                ticker=p.ticker,
                entry_price=p.entry_price,
                current_price=p.current_price,
                sentiment_score=p.sentiment_score,
                momentum_score=p.momentum_score
            ) for p in payload.positions
        ]
        
        internal_candidates = [
            Position(
                ticker=p.ticker,
                entry_price=p.entry_price,
                current_price=p.current_price,
                sentiment_score=p.sentiment_score,
                momentum_score=p.momentum_score
            ) for p in payload.candidates
        ]

        # Execute cycle
        report = await _manager.run_orchestration_cycle(
            positions=internal_positions,
            candidates=internal_candidates,
            headlines=payload.news_headlines
        )
        return {"status": "success", "report": report}

    except Exception as exc:
        logger.exception("Orchestration cycle failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration engine failure: {exc}"
        ) from exc
