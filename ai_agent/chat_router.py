"""
AI Agent — Llama 3.2 Chat Router
=================================
Exposes two endpoints backed by `meta-llama/llama-3.2-3b-instruct:free`:

  POST /ai/chat          — single-turn instruction/chat
  POST /ai/chat/stream   — Server-Sent Events streaming version

Since this is an instruct model, NO reasoning tracking is performed.
Includes OpenRouter ranking headers as requested.
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
from ai_agent.llm_client import get_llama_client, LLMMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Chat — Llama 3.2"])

# OpenRouter headers for rankings
_X_HEADERS = {
    "HTTP-Referer": "https://trading-platform.local",
    "X-OpenRouter-Title": "Institutional Trading Platform",
}


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Payload for /ai/chat."""

    query: str = Field(
        ...,
        examples=["What is the meaning of life?", "Explain RSI divergence."],
        description="User instruction or prompt.",
        max_length=2000,
    )


class ChatResponse(BaseModel):
    """Schema returned by POST /ai/chat."""

    answer: str
    model: str


# ---------------------------------------------------------------------------
# POST /ai/chat
# ---------------------------------------------------------------------------


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="General Chat — Llama 3.2 Instruct",
    description="Standard instruction completion via `llama-3.2-3b-instruct` without CoT.",
    status_code=status.HTTP_200_OK,
)
async def chat(
    payload: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ChatResponse:
    """JWT-gated general chat endpoint."""
    logger.info("Llama chat request · user=%s", current_user.email)

    messages = [LLMMessage(role="user", content=payload.query)]
    client = get_llama_client()

    try:
        # Standard chat (no reasoning argument)
        resp = await client.ask(messages, extra_headers=_X_HEADERS)
    except Exception as exc:
        logger.exception("Llama chat failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Llama 3.2 unavailable: {exc}",
        ) from exc

    return ChatResponse(
        answer=resp.content,
        model=resp.model or "meta-llama/llama-3.2-3b-instruct:free",
    )


# ---------------------------------------------------------------------------
# POST /ai/chat/stream
# ---------------------------------------------------------------------------


@router.post(
    "/chat/stream",
    summary="General Chat (Streaming) — Llama 3.2 Instruct",
    description="Streams the Llama response as Server-Sent Events.",
    response_class=StreamingResponse,
)
async def chat_stream(
    payload: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """JWT-gated SSE streaming endpoint for Llama."""
    logger.info("Llama stream request · user=%s", current_user.email)

    messages = [LLMMessage(role="user", content=payload.query)]
    client = get_llama_client()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # stream_ask returns (text, reasoning_tokens) — reasoning is 0 here
            text, _ = await client.stream_ask(messages, extra_headers=_X_HEADERS)

            chunk_size = 80
            for i in range(0, len(text), chunk_size):
                chunk = text[i : i + chunk_size]
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0)

            yield "data: [DONE]\n\n"

        except Exception as exc:
            logger.exception("Llama stream error: %s", exc)
            yield f"data: [ERROR] {exc}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
