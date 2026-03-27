"""
AI Agent — Liquid LFM-2.5 Thinking Router
==========================================
Exposes two endpoints backed by `liquid/lfm-2.5-1.2b-thinking:free`:

  POST /ai/think          — single-turn fast thinking query
  POST /ai/think/stream   — Server-Sent Events streaming version

The Liquid model is a compact (1.2B) thinking model optimised for speed.
Use it for quick market-context questions; use /ai/analyze (Nemotron) for
deep 2-turn chain-of-thought trade decisions.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.auth.dependencies import get_current_user
from backend.app.models.user import User
from ai_agent.llm_client import get_liquid_client, LLMMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Think — Liquid LFM-2.5"])

# ---------------------------------------------------------------------------
# System prompt — lightweight, fast-path market assistant
# ---------------------------------------------------------------------------

_LIQUID_SYSTEM = """\
You are a fast, concise trading assistant for Indian NSE/BSE markets.
Answer in compact, structured prose. Where applicable, reference SEBI rules.
Do not pad your response.
"""

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ThinkRequest(BaseModel):
    """Payload for /ai/think."""

    query: str = Field(
        ...,
        examples=["What does an inverted hammer candle at resistance imply?"],
        description="Natural-language market or trading question.",
        max_length=800,
    )
    context: str | None = Field(
        default=None,
        examples=["BANKNIFTY is trading at 52-week high with IV=38."],
        description="Optional short market context injected before the query.",
        max_length=400,
    )


class ThinkResponse(BaseModel):
    """Schema returned by POST /ai/think."""

    answer: str
    reasoning_tokens: int
    model: str


# ---------------------------------------------------------------------------
# POST /ai/think — single-turn, non-streaming
# ---------------------------------------------------------------------------


@router.post(
    "/think",
    response_model=ThinkResponse,
    summary="Quick Think — Liquid LFM-2.5",
    description=(
        "Single-turn fast market reasoning via `liquid/lfm-2.5-1.2b-thinking:free`. "
        "Lower latency than /ai/analyze; ideal for quick contextual questions. "
        "Returns the full answer text and reasoning token count."
    ),
    status_code=status.HTTP_200_OK,
)
async def think(
    payload: ThinkRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ThinkResponse:
    """JWT-gated quick-think endpoint."""
    logger.info("Liquid think request · user=%s", current_user.email)

    user_content = (
        f"Context: {payload.context}\n\n{payload.query}" if payload.context else payload.query
    )

    messages = [
        LLMMessage(role="system", content=_LIQUID_SYSTEM),
        LLMMessage(role="user", content=user_content),
    ]

    client = get_liquid_client()
    try:
        resp = await client.ask_with_reasoning(messages)
    except Exception as exc:
        logger.exception("Liquid think failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LFM-2.5 unavailable: {exc}",
        ) from exc

    return ThinkResponse(
        answer=resp.content,
        reasoning_tokens=resp.reasoning_tokens,
        model=resp.model or "liquid/lfm-2.5-1.2b-thinking:free",
    )


# ---------------------------------------------------------------------------
# POST /ai/think/stream — SSE streaming
# ---------------------------------------------------------------------------


@router.post(
    "/think/stream",
    summary="Quick Think (Streaming) — Liquid LFM-2.5",
    description=(
        "Streams the Liquid LFM-2.5 response as Server-Sent Events (text/event-stream). "
        "Each chunk contains a raw text delta. The final chunk carries a "
        "`[DONE] reasoning_tokens=N` marker."
    ),
    response_class=StreamingResponse,
)
async def think_stream(
    payload: ThinkRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """JWT-gated SSE streaming endpoint."""
    logger.info("Liquid stream request · user=%s", current_user.email)

    user_content = (
        f"Context: {payload.context}\n\n{payload.query}" if payload.context else payload.query
    )

    messages = [
        LLMMessage(role="system", content=_LIQUID_SYSTEM),
        LLMMessage(role="user", content=user_content),
    ]

    client = get_liquid_client()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            text, reasoning_tokens = await client.stream_ask(messages)

            # Emit response in ~80-char chunks to simulate real streaming
            chunk_size = 80
            for i in range(0, len(text), chunk_size):
                chunk = text[i : i + chunk_size]
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0)  # yield control to event loop

            # Final marker with reasoning token count
            yield f"data: [DONE] reasoning_tokens={reasoning_tokens}\n\n"

        except Exception as exc:
            logger.exception("Liquid stream error: %s", exc)
            yield f"data: [ERROR] {exc}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
