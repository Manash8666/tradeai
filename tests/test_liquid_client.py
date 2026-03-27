"""
Tests — Liquid LFM-2.5 Thinking Client & Endpoints
====================================================
All LLM calls are mocked — no real API calls are made.
Run with:  python -m pytest tests/test_liquid_client.py -v
"""

from __future__ import annotations

import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, "E:/Trading Platform")

from ai_agent.llm_client import NemotronClient, LLMMessage, LLMResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_liquid_response(
    content: str,
    reasoning_tokens: int = 18,
    model: str = "liquid/lfm-2.5-1.2b-thinking:free",
) -> MagicMock:
    usage = MagicMock()
    usage.prompt_tokens = 30
    usage.completion_tokens = 20
    usage.total_tokens = 50
    usage.reasoning_tokens = reasoning_tokens

    msg = MagicMock()
    msg.content = content
    msg.reasoning_details = []

    choice = MagicMock()
    choice.message = msg

    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    resp.model = model
    return resp


# ---------------------------------------------------------------------------
# 1. get_liquid_client singleton
# ---------------------------------------------------------------------------


class TestGetLiquidClient(unittest.TestCase):

    def test_returns_nemotron_client_instance(self):
        """get_liquid_client() must return a NemotronClient pointed at the Liquid model."""
        import os

        os.environ.setdefault("OPENROUTER_API_KEY", "sk-test-liquid")
        os.environ.setdefault("LIQUID_MODEL", "liquid/lfm-2.5-1.2b-thinking:free")
        os.environ.setdefault("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

        from ai_agent.llm_client import get_liquid_client

        client = get_liquid_client()
        self.assertIsInstance(client, NemotronClient)
        self.assertIn("liquid", client._model)


# ---------------------------------------------------------------------------
# 2. NemotronClient with Liquid model — ask_with_reasoning
# ---------------------------------------------------------------------------


class TestLiquidClientAsk(unittest.IsolatedAsyncioTestCase):

    async def test_ask_with_reasoning_returns_response(self):
        fake = _make_liquid_response(
            "An inverted hammer at resistance signals potential bullish reversal.",
            reasoning_tokens=22,
        )

        client = NemotronClient(
            api_key="sk-test",
            model="liquid/lfm-2.5-1.2b-thinking:free",
        )
        client._client = MagicMock()
        client._client.chat.completions.create = AsyncMock(return_value=fake)

        resp = await client.ask_with_reasoning(
            [LLMMessage(role="user", content="What does an inverted hammer at resistance imply?")]
        )

        self.assertIsInstance(resp, LLMResponse)
        self.assertIn("bullish", resp.content)
        self.assertEqual(resp.reasoning_tokens, 22)

    async def test_stream_ask_returns_text_and_token_count(self):
        """stream_ask must accumulate chunks and return (text, reasoning_tokens)."""

        # Build a fake async iterator of stream chunks
        def _make_chunk(content: str | None, usage=None):
            chunk = MagicMock()
            delta = MagicMock()
            delta.content = content
            choice = MagicMock()
            choice.delta = delta
            chunk.choices = [choice]
            chunk.usage = usage
            return chunk

        usage_obj = MagicMock()
        usage_obj.reasoning_tokens = 15

        chunks = [
            _make_chunk("Liquid"),
            _make_chunk(" is fast."),
            _make_chunk(None, usage=usage_obj),
        ]

        async def fake_aiter(*args, **kwargs):
            for c in chunks:
                yield c

        client = NemotronClient(api_key="sk-test", model="liquid/lfm-2.5-1.2b-thinking:free")
        client._client = MagicMock()
        client._client.chat.completions.create = AsyncMock(return_value=fake_aiter())

        text, tokens = await client.stream_ask([LLMMessage(role="user", content="Quick question.")])

        self.assertEqual(text, "Liquid is fast.")
        self.assertEqual(tokens, 15)


# ---------------------------------------------------------------------------
# 3. /ai/think endpoint — schema & structure
# ---------------------------------------------------------------------------


class TestThinkEndpointSchema(unittest.TestCase):

    def test_think_router_registered(self):
        from ai_agent.thinking_router import router

        paths = [r.path for r in router.routes]
        self.assertIn("/ai/think", paths)
        self.assertIn("/ai/think/stream", paths)

    def test_think_request_schema(self):
        from ai_agent.thinking_router import ThinkRequest
        import pydantic

        # Must fail without query
        with self.assertRaises(pydantic.ValidationError):
            ThinkRequest()

        # Valid with just a query
        req = ThinkRequest(query="What is IV crush?")
        self.assertEqual(req.context, None)

        # Valid with context
        req2 = ThinkRequest(query="Should I sell?", context="NIFTY IV=42")
        self.assertEqual(req2.context, "NIFTY IV=42")

    def test_think_response_schema(self):
        from ai_agent.thinking_router import ThinkResponse

        r = ThinkResponse(
            answer="Sell — IV is elevated.",
            reasoning_tokens=12,
            model="liquid/lfm-2.5-1.2b-thinking:free",
        )
        self.assertEqual(r.reasoning_tokens, 12)

    def test_query_max_length_enforced(self):
        from ai_agent.thinking_router import ThinkRequest
        import pydantic

        with self.assertRaises(pydantic.ValidationError):
            ThinkRequest(query="x" * 801)  # exceeds max_length=800


# ---------------------------------------------------------------------------
# 4. Full think() handler — mocked LLM
# ---------------------------------------------------------------------------


class TestThinkHandler(unittest.IsolatedAsyncioTestCase):

    async def test_think_returns_answer(self):
        fake_resp = _make_liquid_response(
            "IV crush is a sharp drop in implied volatility after an event.",
            reasoning_tokens=9,
        )

        user_mock = MagicMock()
        user_mock.email = "trader@test.com"

        from ai_agent.thinking_router import think, ThinkRequest
        import ai_agent.thinking_router as tr

        original = tr.get_liquid_client

        mock_client = MagicMock()
        mock_client.ask_with_reasoning = AsyncMock(
            return_value=NemotronClient._parse_response(fake_resp)
        )

        try:
            tr.get_liquid_client = lambda: mock_client
            result = await think(
                ThinkRequest(query="What is IV crush?"),
                current_user=user_mock,
            )
        finally:
            tr.get_liquid_client = original

        self.assertIn("IV crush", result.answer)
        self.assertEqual(result.reasoning_tokens, 9)
        self.assertIsInstance(result.model, str)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
