import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import httpx

from backend.app.core.pnl_greed_lock import greed_lock_engine
from backend.app.core.timezone_guards import temporal_guard
from backend.app.config import get_settings

logger = logging.getLogger(__name__)


class LLMHeartbeatTrader:
    """
    Autonomous Heartbeat Agent for Indian Markets (Minimal Information Paradigm).
    Periodically wakes up to evaluate portfolio posture, market regime, and pending signals,
    operating within strict SEBI HITL and Greed Circuit Breaker parameters.
    """

    def __init__(self):
        self.settings = get_settings()
        self.api_key = os.getenv("OPENROUTER_API_KEY", self.settings.openrouter_api_key)
        self.model = self.settings.nemotron_model or "nvidia/nemotron-3-super-120b-a12b:free"
        self.base_url = self.settings.openrouter_base_url
        logger.info("[LLM HEARTBEAT] Initialized autonomous heartbeat monitor.")

    def _determine_session_phase(self, now: datetime) -> str:
        hour = now.hour
        minute = now.minute
        time_val = hour * 60 + minute

        if time_val < 9 * 60:
            return "OVERNIGHT_EARLY"
        elif 9 * 60 <= time_val < 9 * 60 + 15:
            return "PRE_OPEN_AUCTION"
        elif 9 * 60 + 15 <= time_val <= 15 * 60 + 30:
            return "REGULAR_TRADING"
        else:
            return "POST_MARKET"

    async def run_heartbeat_cycle(
        self,
        portfolio: Optional[Dict[str, Any]] = None,
        market_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = temporal_guard.get_market_time()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S IST")
        session_phase = self._determine_session_phase(now)

        portfolio = portfolio or {}
        market_context = market_context or {}

        if not greed_lock_engine.can_execute_trade():
            logger.warning("[LLM HEARTBEAT] Greed Circuit Breaker is active. Terminal hard-locked.")
            return {
                "action": "LOCK",
                "reasoning": f"Terminal locked by Greed Circuit Breaker: {greed_lock_engine.lock_reason}. No operations allowed.",
                "session_phase": session_phase,
                "next_cycle_seconds": 300,
                "ist_time": now_str,
            }

        current_pnl_inr = float(portfolio.get("daily_pnl_inr", 0.0))
        daily_target_inr = float(portfolio.get("daily_target_inr", 50000.0))
        max_drawdown_inr = float(portfolio.get("max_drawdown_inr", -15000.0))
        margin_used_pct = float(portfolio.get("margin_used_pct", 0.0))
        india_vix = float(market_context.get("india_vix", 14.5))
        pending_signals_count = int(market_context.get("pending_hitl_signals", 0))

        if session_phase == "POST_MARKET":
            return {
                "action": "HOLD",
                "reasoning": "NSE/BSE markets closed. Conducting EOD reconciliation; standing by.",
                "session_phase": session_phase,
                "next_cycle_seconds": 600,
                "ist_time": now_str,
            }

        if margin_used_pct > 80.0:
            return {
                "action": "ALERT",
                "reasoning": f"SEBI PTRC Warning: Margin deployment at {margin_used_pct:.1f}% approaching 85% limit. Sizing restricted.",
                "session_phase": session_phase,
                "next_cycle_seconds": 30,
                "ist_time": now_str,
            }

        system_prompt = (
            "You are the autonomous Risk & Execution Heartbeat Agent for an institutional Indian NSE/BSE trading terminal. "
            "Output valid JSON ONLY with keys: action ('SCAN'|'ALERT'|'HOLD'), reasoning (concise 1 sentence), next_cycle_seconds (int)."
        )

        user_content = (
            f"Time IST: {now_str} | Session: {session_phase}\n"
            f"Daily P&L: ₹{current_pnl_inr:,.0f} (Target: ₹{daily_target_inr:,.0f}, MaxDD: ₹{max_drawdown_inr:,.0f})\n"
            f"India VIX: {india_vix:.1f} | Margin Deployed: {margin_used_pct:.1f}%\n"
            f"Pending HITL Advisory Signals: {pending_signals_count}\n"
            f"Recommend next operational step."
        )

        decision = {
            "action": "SCAN" if session_phase == "REGULAR_TRADING" else "HOLD",
            "reasoning": f"Session {session_phase} active. Maintaining tactical vigilance.",
            "session_phase": session_phase,
            "next_cycle_seconds": 45 if session_phase == "REGULAR_TRADING" else 180,
            "ist_time": now_str,
        }

        if self.api_key and not self.api_key.startswith("mock_"):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://tradingplatform.in",
                    "X-Title": "Institutional Indian AI Trading Platform",
                }
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "max_tokens": 120,
                    "temperature": 0.2,
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip()
                        if content.startswith("```"):
                            content = content.split("```")[1]
                            if content.startswith("json"):
                                content = content[4:]
                        parsed = json.loads(content)
                        decision["action"] = parsed.get("action", decision["action"])
                        decision["reasoning"] = parsed.get("reasoning", decision["reasoning"])
                        decision["next_cycle_seconds"] = parsed.get("next_cycle_seconds", decision["next_cycle_seconds"])
            except Exception as e:
                logger.debug(f"[LLM HEARTBEAT] OpenRouter fallback engaged: {e}")

        logger.info(f"[LLM HEARTBEAT] Action: {decision['action']} | Reasoning: {decision['reasoning']}")
        return decision
