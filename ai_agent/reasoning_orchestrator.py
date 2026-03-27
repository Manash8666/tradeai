"""
NemotronReasoningOrchestrator
==============================
High-level coordinator that runs a **two-turn chain-of-thought** using the
Nemotron-Super model on top of the existing AutonomousSwarmOrchestrator votes.

Turn 1 — Context + Query
    The swarm's deterministic votes (momentum, EPS, volatility) are embedded
    into the first message alongside the user query.  Reasoning is enabled so
    the model produces a detailed internal trace before answering.

Turn 2 — SEBI Confidence Challenge
    The assistant's full reply (content + reasoning_details) is preserved and
    passed back unchanged.  A follow-up message challenges the model to
    re-evaluate under SEBI risk and position-sizing constraints, producing a
    final refined signal.

Returns a `TradeRecommendation` dataclass with all fields required for the
audit trail and for the `/ai/analyze` API response.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ai_agent.agent_swarm import AutonomousSwarmOrchestrator
from ai_agent.llm_client import NemotronClient, LLMMessage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output type
# ---------------------------------------------------------------------------


@dataclass
class TradeRecommendation:
    """
    Structured output from the two-turn Nemotron reasoning chain.
    Serialisable to JSON for the API response and audit log.
    """

    ticker: str
    signal: str  # "BUY" | "SELL" | "HOLD"
    confidence: float  # 0.0 – 1.0
    swarm_consensus: str  # Raw vote from AutonomousSwarmOrchestrator
    swarm_confidence: float
    llm_rationale: str  # Final answer text from Turn 2
    reasoning_tokens: int = 0
    turn1_reasoning_tokens: int = 0
    agent_logs: list[str] = field(default_factory=list)
    model: str = "nvidia/nemotron-3-super-120b-a12b:free"


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

# System prompt — concise, deterministic, SEBI-aware
_SYSTEM_PROMPT = """\
You are Arjun, an institutional trading intelligence for Indian NSE/BSE derivatives.
You receive structured market signals from an internal quant swarm and must reason
carefully before issuing a directional trade recommendation.

Rules you must always follow:
1. Signal outputs must be exactly one of: BUY, SELL, or HOLD.
2. Confidence must be a float between 0.00 and 1.00.
3. Any recommendation must respect SEBI ALGO-TRADING guidelines:
   - No position should exceed 20% of the account's notional value.
   - Volatility above IV=40 requires automatic HOLD unless risk is qualified.
4. Output a final JSON block at the very end in this exact format:
   ```json
   {"signal": "BUY", "confidence": 0.87}
   ```
"""

# Challenge prompt — appended as the second user turn
_SEBI_CHALLENGE = (
    "Please review your recommendation carefully. "
    "Consider SEBI position-sizing limits (max 20% notional), "
    "the implied volatility regime, and whether the opportunity is robust "
    "to a 10% adverse price move. "
    "Confirm or revise your earlier answer and re-state the final JSON block."
)


class NemotronReasoningOrchestrator:
    """
    Combines deterministic swarm signals with Nemotron's chain-of-thought
    to produce an auditable trade recommendation.
    """

    def __init__(self, llm_client: NemotronClient) -> None:
        self._llm = llm_client
        self._swarm = AutonomousSwarmOrchestrator(use_strict_mode=True)
        logger.info("NemotronReasoningOrchestrator ready.")

    async def analyze_trade_setup(
        self,
        ticker: str,
        market_data: dict[str, Any],
        query: str,
    ) -> TradeRecommendation:
        """
        Run the full two-turn reasoning chain and return a TradeRecommendation.

        Parameters
        ----------
        ticker      : NSE/BSE instrument symbol, e.g. "NIFTY50"
        market_data : Dict with keys momentum, earnings_surprise, volatility (+ extras)
        query       : Natural-language question from the trader
        """
        # ------------------------------------------------------------------
        # Step 0 — Swarm consensus (deterministic, cheap)
        # ------------------------------------------------------------------
        swarm_result = self._swarm.run_swarm_consensus(ticker, market_data)
        logger.info(
            "[%s] Swarm → %s @ %.4f confidence",
            ticker,
            swarm_result["consensus"],
            swarm_result["swarm_confidence"],
        )

        # ------------------------------------------------------------------
        # Step 1 — Build Turn-1 prompt
        # ------------------------------------------------------------------
        context_block = (
            f"Ticker: {ticker}\n"
            f"Market Data: {market_data}\n"
            f"Swarm Consensus: {swarm_result['consensus']} "
            f"(confidence={swarm_result['swarm_confidence']:.4f})\n"
            f"Agent Logs:\n" + "\n".join(f"  {log}" for log in swarm_result["agent_logs"])
        )

        turn1_user_content = (
            f"{context_block}\n\n"
            f"Trader Query: {query}\n\n"
            "Think step-by-step about whether you agree with the swarm's consensus "
            "and provide your analysis. End with the required JSON signal block."
        )

        messages_turn1: list[LLMMessage] = [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
            LLMMessage(role="user", content=turn1_user_content),
        ]

        # ------------------------------------------------------------------
        # Step 2 — Turn 1: Reasoning enabled
        # ------------------------------------------------------------------
        logger.debug("[%s] Sending Turn 1 to Nemotron…", ticker)
        resp1 = await self._llm.ask_with_reasoning(messages_turn1)
        logger.info(
            "[%s] Turn 1 complete · reasoning_tokens=%d",
            ticker,
            resp1.reasoning_tokens,
        )

        # ------------------------------------------------------------------
        # Step 3 — Build Turn-2 prompt (preserve reasoning_details)
        # ------------------------------------------------------------------
        messages_turn2: list[LLMMessage] = [
            *messages_turn1,
            LLMMessage(
                role="assistant",
                content=resp1.content,
                reasoning_details=resp1.reasoning_details or [],
            ),
            LLMMessage(role="user", content=_SEBI_CHALLENGE),
        ]

        # ------------------------------------------------------------------
        # Step 4 — Turn 2: Continue reasoning chain
        # ------------------------------------------------------------------
        logger.debug("[%s] Sending Turn 2 to Nemotron…", ticker)
        resp2 = await self._llm.ask_with_reasoning(messages_turn2)
        logger.info(
            "[%s] Turn 2 complete · reasoning_tokens=%d",
            ticker,
            resp2.reasoning_tokens,
        )

        # ------------------------------------------------------------------
        # Step 5 — Parse final JSON signal block from Turn-2 response
        # ------------------------------------------------------------------
        signal, confidence = _extract_signal_json(
            resp2.content,
            fallback_signal=swarm_result["consensus"],
            fallback_confidence=swarm_result["swarm_confidence"],
        )

        return TradeRecommendation(
            ticker=ticker,
            signal=signal,
            confidence=confidence,
            swarm_consensus=swarm_result["consensus"],
            swarm_confidence=swarm_result["swarm_confidence"],
            llm_rationale=resp2.content,
            reasoning_tokens=resp2.reasoning_tokens,
            turn1_reasoning_tokens=resp1.reasoning_tokens,
            agent_logs=swarm_result["agent_logs"],
            model=resp2.model or "nvidia/nemotron-3-super-120b-a12b:free",
        )


# ---------------------------------------------------------------------------
# Helper — parse the JSON signal block from LLM output
# ---------------------------------------------------------------------------


def _extract_signal_json(
    text: str,
    fallback_signal: str = "HOLD",
    fallback_confidence: float = 0.5,
) -> tuple[str, float]:
    """
    Locate the ```json ... ``` block emitted by the model and extract
    `signal` and `confidence`.  Falls back to the swarm values on any
    parse error so the endpoint never crashes.
    """
    import json
    import re

    # Try fenced JSON block first
    pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if not match:
        # Try raw JSON anywhere in the text
        match = re.search(r'\{\s*"signal"\s*:', text, re.DOTALL)
        if match:
            # Try to find closing brace
            candidate = text[match.start() :]
            try:
                data = json.loads(candidate[: candidate.index("}") + 1])
                return _validated(data, fallback_signal, fallback_confidence)
            except Exception:
                pass
        logger.warning("No JSON signal block found in LLM response — using swarm fallback.")
        return fallback_signal, fallback_confidence

    try:
        data = json.loads(match.group(1))
        return _validated(data, fallback_signal, fallback_confidence)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse error in LLM signal block: %s", exc)
        return fallback_signal, fallback_confidence


def _validated(
    data: dict,
    fallback_signal: str,
    fallback_confidence: float,
) -> tuple[str, float]:
    signal = data.get("signal", fallback_signal).upper()
    if signal not in {"BUY", "SELL", "HOLD"}:
        signal = fallback_signal

    confidence = float(data.get("confidence", fallback_confidence))
    confidence = max(0.0, min(1.0, confidence))

    return signal, confidence
