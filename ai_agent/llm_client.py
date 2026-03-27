"""
NemotronClient — OpenRouter LLM Client
======================================
Thin async wrapper around the OpenAI Python SDK pointed at OpenRouter,
targeting nvidia/nemotron-3-super-120b-a12b:free.

Features
--------
* Single-shot chat (`ask`)
* Reasoning-enabled chat with `reasoning_details` preserved (`ask_with_reasoning`)
* Streaming with usage/reasoning-token reporting (`stream_ask`)
* Config-driven — reads key/model/timeout/retries from Settings; never hardcodes secrets
* Automatic retry with exponential back-off (tenacity)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import AsyncIterator, Any

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class LLMMessage:
    """A single message in a chat conversation."""
    role: str  # "system" | "user" | "assistant"
    content: str
    reasoning_details: list[dict] | None = field(default=None)


@dataclass
class LLMResponse:
    """Structured response from the LLM."""
    content: str
    reasoning_details: list[dict] = field(default_factory=list)
    reasoning_tokens: int = 0
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class NemotronClient:
    """
    Async LLM client for nvidia/nemotron-3-super-120b-a12b via OpenRouter.

    Instantiate once at application startup and reuse (thread-safe via asyncio).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/nemotron-3-super-120b-a12b:free",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 60,
        max_retries: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Add it to your .env file before starting the server."
            )
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=0,  # We handle retries ourselves below
        )
        logger.info(
            "NemotronClient initialised · model=%s · base_url=%s",
            model,
            base_url,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ask(self, messages: list[LLMMessage], extra_headers: dict | None = None) -> LLMResponse:
        """
        Single-shot chat completion (no reasoning mode).
        Suitable for classification, summarisation, quick Q&A.
        """
        kwargs = {
            "model": self._model,
            "messages": self._serialise(messages)
        }
        if extra_headers:
            kwargs["extra_headers"] = extra_headers

        raw = await self._with_retry(
            self._client.chat.completions.create(**kwargs)
        )
        return self._parse_response(raw)

    async def ask_with_reasoning(self, messages: list[LLMMessage], extra_headers: dict | None = None) -> LLMResponse:
        """
        Chat completion with extended thinking enabled.
        Returns reasoning_details so multi-turn reasoning chains work correctly.
        """
        kwargs = {
            "model": self._model,
            "messages": self._serialise(messages),
            "extra_body": {"reasoning": {"enabled": True}},
        }
        if extra_headers:
            kwargs["extra_headers"] = extra_headers

        raw = await self._with_retry(
            self._client.chat.completions.create(**kwargs)
        )
        return self._parse_response(raw)

    async def stream_ask(self, messages: list[LLMMessage], extra_headers: dict | None = None) -> tuple[str, int]:
        """
        Streaming chat — accumulates the full response text and returns
        (full_text, reasoning_tokens).  Useful for server-sent events.
        """
        response_text = ""
        reasoning_tokens_count = 0

        kwargs = {
            "model": self._model,
            "messages": self._serialise(messages),
            "stream": True,
            "stream_options": {"include_usage": True},
            "extra_body": {"reasoning": {"enabled": True}},
        }
        if extra_headers:
            kwargs["extra_headers"] = extra_headers

        stream = await self._with_retry(
            self._client.chat.completions.create(**kwargs)
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                response_text += delta.content

            # Final chunk carries usage data
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage
                reasoning_tokens_count = getattr(usage, "reasoning_tokens", 0) or 0

        logger.debug(
            "stream_ask complete · chars=%d · reasoning_tokens=%d",
            len(response_text),
            reasoning_tokens_count,
        )
        return response_text, reasoning_tokens_count

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialise(messages: list[LLMMessage]) -> list[dict]:
        """Convert LLMMessage dataclasses to OpenAI-compatible dicts."""
        result = []
        for msg in messages:
            entry: dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.reasoning_details is not None:
                entry["reasoning_details"] = msg.reasoning_details
            result.append(entry)
        return result

    @staticmethod
    def _parse_response(raw: Any) -> LLMResponse:
        """Extract structured data from a raw OpenAI completion object."""
        choice = raw.choices[0]
        msg = choice.message

        content = msg.content or ""
        reasoning_details = getattr(msg, "reasoning_details", None) or []
        usage_obj = getattr(raw, "usage", None)
        usage_dict = {}
        reasoning_tokens = 0

        if usage_obj:
            usage_dict = {
                "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
                "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
                "total_tokens": getattr(usage_obj, "total_tokens", 0),
            }
            reasoning_tokens = getattr(usage_obj, "reasoning_tokens", 0) or 0

        return LLMResponse(
            content=content,
            reasoning_details=reasoning_details,
            reasoning_tokens=reasoning_tokens,
            model=getattr(raw, "model", ""),
            usage=usage_dict,
        )

    async def _with_retry(self, coro_or_awaitable: Any) -> Any:
        """Execute an awaitable with exponential back-off on transient errors."""
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return await coro_or_awaitable
            except RateLimitError as exc:
                wait = 2 ** attempt
                logger.warning(
                    "Rate limited by OpenRouter (attempt %d/%d). Retrying in %ds…",
                    attempt, self._max_retries, wait,
                )
                last_exc = exc
                await asyncio.sleep(wait)
            except APIConnectionError as exc:
                wait = 2 ** attempt
                logger.warning(
                    "Connection error (attempt %d/%d). Retrying in %ds… %s",
                    attempt, self._max_retries, wait, exc,
                )
                last_exc = exc
                await asyncio.sleep(wait)
            except APIError as exc:
                # Non-transient API error — raise immediately
                logger.error("OpenRouter API error: %s", exc)
                raise

        raise RuntimeError(
            f"LLM call failed after {self._max_retries} retries."
        ) from last_exc


# ---------------------------------------------------------------------------
# Application-level singleton factory
# ---------------------------------------------------------------------------

_client_instance: NemotronClient | None = None


def get_nemotron_client() -> NemotronClient:
    """
    FastAPI dependency / singleton accessor.
    Reads config lazily so the Settings cache is already populated.
    """
    global _client_instance
    if _client_instance is None:
        from backend.app.config import get_settings  # local import to avoid cycles
        s = get_settings()
        _client_instance = NemotronClient(
            api_key=s.openrouter_api_key,
            model=s.nemotron_model,
            base_url=s.openrouter_base_url,
            timeout=s.llm_request_timeout,
            max_retries=s.llm_max_retries,
        )
    return _client_instance


_liquid_client_instance: NemotronClient | None = None


def get_liquid_client() -> NemotronClient:
    """
    Singleton for the Liquid LFM-2.5 thinking model.
    Uses the same NemotronClient infrastructure — only the model string differs.
    """
    global _liquid_client_instance
    if _liquid_client_instance is None:
        from backend.app.config import get_settings
        s = get_settings()
        _liquid_client_instance = NemotronClient(
            api_key=s.openrouter_api_key,
            model=s.liquid_model,
            base_url=s.openrouter_base_url,
            timeout=s.llm_request_timeout,
            max_retries=s.llm_max_retries,
        )
    return _liquid_client_instance


_llama_client_instance: NemotronClient | None = None


def get_llama_client() -> NemotronClient:
    """
    Singleton for the Llama 3.2 3B Instruct model.
    """
    global _llama_client_instance
    if _llama_client_instance is None:
        from backend.app.config import get_settings
        s = get_settings()
        _llama_client_instance = NemotronClient(
            api_key=s.openrouter_api_key,
            model=s.llama_model,
            base_url=s.openrouter_base_url,
            timeout=s.llm_request_timeout,
            max_retries=s.llm_max_retries,
        )
    return _llama_client_instance
