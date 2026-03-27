"""
AI Agent — FastAPI Router
==========================
Exposes `POST /ai/analyze` — the authenticated endpoint that runs the
NemotronReasoningOrchestrator and returns a full TradeRecommendation.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.auth.dependencies import get_current_user
from backend.app.models.user import User
from ai_agent.llm_client import get_nemotron_client
from ai_agent.reasoning_orchestrator import (
    NemotronReasoningOrchestrator,
    TradeRecommendation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Payload for the /ai/analyze endpoint."""
    ticker: str = Field(
        ...,
        examples=["NIFTY50"],
        description="NSE/BSE instrument symbol.",
    )
    market_data: dict[str, Any] = Field(
        ...,
        examples=[{"momentum": 0.45, "earnings_surprise": 0.12, "volatility": 28}],
        description=(
            "Structured market metrics passed to both the swarm and the LLM. "
            "Required keys: momentum (float), earnings_surprise (float), "
            "volatility (float, IV %). Additional keys are forwarded as context."
        ),
    )
    query: str = Field(
        ...,
        examples=["Should I enter a long NIFTY position today?"],
        description="Natural-language trade question from the trader.",
        max_length=500,
    )


class AnalyzeResponse(BaseModel):
    """Schema returned by /ai/analyze."""
    ticker: str
    signal: str = Field(description="BUY | SELL | HOLD")
    confidence: float = Field(description="0.0 – 1.0")
    swarm_consensus: str
    swarm_confidence: float
    llm_rationale: str
    reasoning_tokens: int
    turn1_reasoning_tokens: int
    agent_logs: list[str]
    model: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="AI Trade Analysis — Nemotron 2-Turn Reasoning",
    description=(
        "Runs the AutonomousSwarmOrchestrator deterministic vote and then "
        "passes the result through two rounds of Nemotron-Super chain-of-thought "
        "reasoning before returning a final auditable trade recommendation."
    ),
    status_code=status.HTTP_200_OK,
)
async def analyze_trade(
    payload: AnalyzeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalyzeResponse:
    """
    Authenticated endpoint — requires a valid JWT access token.
    Calls the NemotronReasoningOrchestrator and returns a TradeRecommendation.
    """
    logger.info(
        "AI analyze request · ticker=%s · user=%s",
        payload.ticker,
        current_user.email,
    )

    # Validate required market_data keys
    required_keys = {"momentum", "earnings_surprise", "volatility"}
    missing = required_keys - set(payload.market_data.keys())
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"market_data missing required keys: {sorted(missing)}",
        )

    # Build orchestrator with injected LLM client
    llm_client = get_nemotron_client()
    orchestrator = NemotronReasoningOrchestrator(llm_client=llm_client)

    try:
        rec: TradeRecommendation = await orchestrator.analyze_trade_setup(
            ticker=payload.ticker,
            market_data=payload.market_data,
            query=payload.query,
        )
    except Exception as exc:
        logger.exception("LLM analysis failed for ticker=%s: %s", payload.ticker, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM analysis unavailable: {exc}",
        ) from exc

    return AnalyzeResponse(
        ticker=rec.ticker,
        signal=rec.signal,
        confidence=rec.confidence,
        swarm_consensus=rec.swarm_consensus,
        swarm_confidence=rec.swarm_confidence,
        llm_rationale=rec.llm_rationale,
        reasoning_tokens=rec.reasoning_tokens,
        turn1_reasoning_tokens=rec.turn1_reasoning_tokens,
        agent_logs=rec.agent_logs,
        model=rec.model,
    )
