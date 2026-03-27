"""
Tests — Llama 3.2 Chat Client & Endpoints
==========================================
All calls are mocked.
Run with:  python -m pytest tests/test_llama_client.py -v
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


def _make_llama_response(content: str) -> MagicMock:
    usage = MagicMock()
    usage.prompt_tokens = 20
    usage.completion_tokens = 30
    usage.total_tokens = 50
    # Instruct models don't return reasoning tokens
    usage.reasoning_tokens = 0

    msg = MagicMock()
    msg.content = content
    msg.reasoning_details = []

    choice = MagicMock()
    choice.message = msg

    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    resp.model = "meta-llama/llama-3.2-3b-instruct:free"
    return resp


# ---------------------------------------------------------------------------
# 1. get_llama_client singleton
# ---------------------------------------------------------------------------


class TestGetLlamaClient(unittest.TestCase):

    def test_returns_nemotron_client_instance(self):
        """get_llama_client() returns NemotronClient pointed at Llama model."""
        import os

        os.environ.setdefault("OPENROUTER_API_KEY", "sk-test-llama")
        os.environ.setdefault("LLAMA_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
        os.environ.setdefault("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

        from ai_agent.llm_client import get_llama_client

        client = get_llama_client()
        self.assertIsInstance(client, NemotronClient)
        self.assertIn("llama", client._model)


# ---------------------------------------------------------------------------
# 2. Client .ask() — headers injection
# ---------------------------------------------------------------------------


class TestLlamaClientAsk(unittest.IsolatedAsyncioTestCase):

    async def test_ask_with_extra_headers(self):
        fake = _make_llama_response("42 is the answer.")

        client = NemotronClient(
            api_key="sk-test",
            model="meta-llama/llama-3.2-3b-instruct:free",
        )
        client._client = MagicMock()
        client._client.chat.completions.create = AsyncMock(return_value=fake)

        headers = {"X-Custom": "Test"}
        resp = await client.ask(
            [LLMMessage(role="user", content="Meaning of life?")], extra_headers=headers
        )

        self.assertIsInstance(resp, LLMResponse)
        self.assertEqual(resp.content, "42 is the answer.")
        self.assertEqual(resp.reasoning_tokens, 0)

        # Assert extra_headers was structurally injected into kwargs
        kwargs = client._client.chat.completions.create.call_args.kwargs
        self.assertIn("extra_headers", kwargs)
        self.assertEqual(kwargs["extra_headers"]["X-Custom"], "Test")


# ---------------------------------------------------------------------------
# 3. /ai/chat endpoint tests
# ---------------------------------------------------------------------------


class TestChatEndpointSchema(unittest.TestCase):

    def test_chat_router_registered(self):
        from ai_agent.chat_router import router

        paths = [r.path for r in router.routes]
        self.assertIn("/ai/chat", paths)
        self.assertIn("/ai/chat/stream", paths)

    def test_chat_request_schema(self):
        from ai_agent.chat_router import ChatRequest
        import pydantic

        with self.assertRaises(pydantic.ValidationError):
            ChatRequest()

        req = ChatRequest(query="Hello")
        self.assertEqual(req.query, "Hello")


class TestChatHandler(unittest.IsolatedAsyncioTestCase):

    async def test_chat_returns_answer(self):
        fake_resp = _make_llama_response("Hello, I am Llama.")

        user_mock = MagicMock()
        user_mock.email = "trader@test.com"

        from ai_agent.chat_router import chat, ChatRequest
        import ai_agent.chat_router as cr

        original = cr.get_llama_client

        mock_client = MagicMock()
        mock_client.ask = AsyncMock(return_value=NemotronClient._parse_response(fake_resp))

        try:
            cr.get_llama_client = lambda: mock_client
            result = await chat(ChatRequest(query="Who are you?"), user_mock)
        finally:
            cr.get_llama_client = original

        self.assertEqual(result.answer, "Hello, I am Llama.")
        self.assertIn("llama", result.model)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main()
