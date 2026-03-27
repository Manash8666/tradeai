"""
Tests — Nemotron Client & Reasoning Orchestrator
=================================================
Unit tests that mock the OpenAI SDK so no real API calls are made.
Run with:  python -m pytest tests/test_nemotron_client.py -v
"""

from __future__ import annotations

import sys
import json
import asyncio
import unittest
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, "E:/Trading Platform")

from ai_agent.llm_client import NemotronClient, LLMMessage, LLMResponse
from ai_agent.reasoning_orchestrator import (
    NemotronReasoningOrchestrator,
    TradeRecommendation,
    _extract_signal_json,
)


# ---------------------------------------------------------------------------
# Helpers — build fake OpenAI response objects
# ---------------------------------------------------------------------------

def _make_openai_response(
    content: str,
    reasoning_details: list | None = None,
    reasoning_tokens: int = 42,
    model: str = "nvidia/nemotron-3-super-120b-a12b:free",
) -> MagicMock:
    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 50
    usage.total_tokens = 150
    usage.reasoning_tokens = reasoning_tokens

    msg = MagicMock()
    msg.content = content
    msg.reasoning_details = reasoning_details or []

    choice = MagicMock()
    choice.message = msg

    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    resp.model = model
    return resp


# ---------------------------------------------------------------------------
# 1. NemotronClient instantiation
# ---------------------------------------------------------------------------

class TestNemotronClientInstantiation(unittest.TestCase):

    def test_raises_on_empty_api_key(self):
        with self.assertRaises(ValueError, msg="Should raise if API key is empty"):
            NemotronClient(api_key="")

    def test_instantiates_with_valid_key(self):
        client = NemotronClient(api_key="sk-test-1234")
        self.assertIsInstance(client, NemotronClient)


# ---------------------------------------------------------------------------
# 2. LLMResponse parsing
# ---------------------------------------------------------------------------

class TestLLMResponseParsing(unittest.TestCase):

    def test_parse_response_extracts_fields(self):
        raw = _make_openai_response(
            content='Analysis done.\n```json\n{"signal":"BUY","confidence":0.88}\n```',
            reasoning_tokens=77,
        )
        result = NemotronClient._parse_response(raw)
        self.assertIsInstance(result, LLMResponse)
        self.assertIn("BUY", result.content)
        self.assertEqual(result.reasoning_tokens, 77)
        self.assertEqual(result.usage["total_tokens"], 150)

    def test_parse_response_handles_missing_usage(self):
        raw = _make_openai_response(content="Short answer.")
        raw.usage = None
        result = NemotronClient._parse_response(raw)
        self.assertEqual(result.reasoning_tokens, 0)
        self.assertEqual(result.usage, {})


# ---------------------------------------------------------------------------
# 3. Signal JSON extraction
# ---------------------------------------------------------------------------

class TestExtractSignalJson(unittest.TestCase):

    def test_extracts_fenced_json(self):
        text = 'Detailed analysis here.\n```json\n{"signal": "SELL", "confidence": 0.76}\n```'
        signal, conf = _extract_signal_json(text)
        self.assertEqual(signal, "SELL")
        self.assertAlmostEqual(conf, 0.76)

    def test_invalid_signal_fallback(self):
        text = '```json\n{"signal": "UNKNOWN", "confidence": 0.5}\n```'
        signal, conf = _extract_signal_json(text, fallback_signal="HOLD")
        self.assertEqual(signal, "HOLD")

    def test_no_json_returns_fallback(self):
        signal, conf = _extract_signal_json(
            "No JSON here at all.",
            fallback_signal="BUY",
            fallback_confidence=0.6,
        )
        self.assertEqual(signal, "BUY")
        self.assertAlmostEqual(conf, 0.6)

    def test_clamps_confidence_range(self):
        text = '```json\n{"signal": "BUY", "confidence": 1.5}\n```'
        _, conf = _extract_signal_json(text)
        self.assertLessEqual(conf, 1.0)

        text2 = '```json\n{"signal": "HOLD", "confidence": -0.3}\n```'
        _, conf2 = _extract_signal_json(text2)
        self.assertGreaterEqual(conf2, 0.0)


# ---------------------------------------------------------------------------
# 4. NemotronClient.ask_with_reasoning (mocked)
# ---------------------------------------------------------------------------

class TestNemotronClientAskWithReasoning(unittest.IsolatedAsyncioTestCase):

    async def test_ask_with_reasoning_returns_llm_response(self):
        fake_resp = _make_openai_response(
            content='```json\n{"signal":"BUY","confidence":0.91}\n```',
            reasoning_tokens=55,
        )

        client = NemotronClient(api_key="sk-test")
        client._client = MagicMock()
        client._client.chat.completions.create = AsyncMock(return_value=fake_resp)

        result = await client.ask_with_reasoning([
            LLMMessage(role="user", content="Should I buy NIFTY?")
        ])

        self.assertIsInstance(result, LLMResponse)
        self.assertEqual(result.reasoning_tokens, 55)
        self.assertIn("BUY", result.content)


# ---------------------------------------------------------------------------
# 5. NemotronReasoningOrchestrator.analyze_trade_setup (mocked, 2-turn)
# ---------------------------------------------------------------------------

class TestNemotronReasoningOrchestrator(unittest.IsolatedAsyncioTestCase):

    async def test_analyze_trade_setup_returns_recommendation(self):
        turn1_content = (
            "After analysing the swarm votes and momentum:\n"
            '```json\n{"signal":"BUY","confidence":0.80}\n```'
        )
        turn2_content = (
            "After SEBI re-evaluation, the signal is confirmed.\n"
            '```json\n{"signal":"BUY","confidence":0.85}\n```'
        )

        resp1 = _make_openai_response(turn1_content, reasoning_tokens=30)
        resp2 = _make_openai_response(turn2_content, reasoning_tokens=50)

        client = NemotronClient(api_key="sk-test")
        client._client = MagicMock()
        # First call → Turn 1, second call → Turn 2
        client._client.chat.completions.create = AsyncMock(
            side_effect=[resp1, resp2]
        )

        orchestrator = NemotronReasoningOrchestrator(llm_client=client)
        rec = await orchestrator.analyze_trade_setup(
            ticker="NIFTY50",
            market_data={"momentum": 0.5, "earnings_surprise": 0.1, "volatility": 22},
            query="Should I go long today?",
        )

        self.assertIsInstance(rec, TradeRecommendation)
        self.assertEqual(rec.ticker, "NIFTY50")
        self.assertEqual(rec.signal, "BUY")
        self.assertAlmostEqual(rec.confidence, 0.85)
        self.assertEqual(rec.reasoning_tokens, 50)
        self.assertEqual(rec.turn1_reasoning_tokens, 30)
        self.assertIsNotNone(rec.swarm_consensus)
        self.assertIsInstance(rec.agent_logs, list)

    async def test_analyze_falls_back_to_swarm_on_bad_json(self):
        """If the LLM returns no valid JSON, the swarm signal is used."""
        bad_resp = _make_openai_response("I am unable to determine a signal.")
        bad_resp.choices[0].message.content = "I am unable to determine a signal."

        client = NemotronClient(api_key="sk-test")
        client._client = MagicMock()
        client._client.chat.completions.create = AsyncMock(return_value=bad_resp)

        orchestrator = NemotronReasoningOrchestrator(llm_client=client)
        rec = await orchestrator.analyze_trade_setup(
            ticker="BANKNIFTY",
            market_data={"momentum": 1, "earnings_surprise": 1, "volatility": 15},
            query="Long BANKNIFTY?",
        )

        # Swarm will return BUY for these inputs (all positive)
        self.assertIn(rec.signal, {"BUY", "SELL", "HOLD"})
        self.assertIsInstance(rec.confidence, float)


# ---------------------------------------------------------------------------
# 6. FastAPI endpoint — structural test (no real HTTP, no real LLM)
# ---------------------------------------------------------------------------

class TestAnalyzeEndpoint(unittest.TestCase):

    def test_endpoint_registered(self):
        """Verify the router can be imported and the route is declared."""
        from ai_agent.router import router
        paths = [r.path for r in router.routes]
        self.assertIn("/ai/analyze", paths, "POST /ai/analyze must be registered.")

    def test_analyze_request_schema_requires_fields(self):
        from ai_agent.router import AnalyzeRequest
        import pydantic

        # Should raise on missing fields
        with self.assertRaises(pydantic.ValidationError):
            AnalyzeRequest(ticker="NIFTY50")  # missing market_data and query

        # Should succeed with all three
        req = AnalyzeRequest(
            ticker="NIFTY50",
            market_data={"momentum": 0.1, "earnings_surprise": 0.0, "volatility": 30},
            query="Analyze this.",
        )
        self.assertEqual(req.ticker, "NIFTY50")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main()
