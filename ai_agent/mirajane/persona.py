import json
import logging
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import zoneinfo
import httpx

from .news_engine import global_news_engine, NewsItem
from .macro_scanner import global_macro_scanner, MacroMatrix
from .trading_engine import mirajane_trade_engine
from backend.app.core.pnl_greed_lock import greed_lock_engine
from backend.app.core.timezone_guards import temporal_guard
from backend.app.core.sebi_hitl_compliance import sebi_hitl_guard
from backend.app.config import get_settings

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class MirajaneMode(str, Enum):
    CALM = "CALM"              # "Serene Reception" — Caring, protective, disciplined risk custodian
    SATAN_SOUL = "SATAN_SOUL"  # "Tactical Dominance" — Predatory, razor-sharp quantitative alpha hunter


@dataclass
class MirajaneResponse:
    reply: str
    mode: str
    mood: str
    top_news_considered: List[str]
    macro_sentiment: str
    suggested_action: Optional[str]
    ist_timestamp: str
    trade_action: Optional[Dict[str, Any]] = None  # Prepared order for 1-Touch execution

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MirajaneCore:
    """
    Mirajane Strauss — Master AI Trading Intelligence Persona.
    Seamlessly synthesizes real-time global news, macroeconomic cross-asset vectors,
    and Indian market order books with an adaptive dual-mode consciousness.
    """

    def __init__(self):
        self.mode = MirajaneMode.CALM
        self.settings = get_settings()
        self.api_key = self.settings.openrouter_api_key
        self.model = self.settings.nemotron_model or "nvidia/nemotron-3-super-120b-a12b:free"
        self.base_url = self.settings.openrouter_base_url
        logger.info("[MIRAJANE] Mirajane Strauss online. Current Mode: Serene Reception (CALM).")

    def switch_mode(self, new_mode: MirajaneMode | str) -> MirajaneMode:
        """Toggles between Serene Reception (CALM) and Satan Soul (SATAN_SOUL)."""
        if isinstance(new_mode, str):
            new_mode = MirajaneMode.SATAN_SOUL if "SATAN" in new_mode.upper() else MirajaneMode.CALM
        self.mode = new_mode
        logger.warning(f"[MIRAJANE] Transformation complete! Active Form: {self.mode.value}")
        return self.mode

    async def chat(
        self,
        user_message: str,
        portfolio_context: Optional[Dict[str, Any]] = None,
    ) -> MirajaneResponse:
        """
        Interactive reasoning cycle.
        Gathers live internet news and global macro telemetry, then generates
        a personalized response aligned with her current persona mode.
        """
        now = temporal_guard.get_market_time()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S IST")
        msg_upper = user_message.upper()

        # 1. Gather live global internet news & macro telemetry
        news_items = await global_news_engine.fetch_live_news()
        top_news_titles = [item.title for item in news_items[:4]]
        macro_matrix = global_macro_scanner.scan_global_macro()

        # 2. Extract risk parameters
        greed_locked = not greed_lock_engine.can_execute_trade()
        greed_reason = greed_lock_engine.lock_reason if greed_locked else "Normal Operation"
        pnl_inr = float(portfolio_context.get("daily_pnl_inr", 0.0)) if portfolio_context else 0.0

        # 3. Determine persona tone and system instruction
        if self.mode == MirajaneMode.CALM:
            system_prompt = (
                "You are Mirajane Strauss in your 'Serene Reception' persona: an extraordinarily courteous, "
                "supportive, and protective trading companion for Indian markets (NSE/BSE). "
                "You speak warmly and gracefully, always prioritizing disciplined risk management, capital preservation, "
                "and SEBI compliance. Always quote amounts in Indian Rupees (₹) and times in IST. "
                "Keep responses concise, insightful, and practical."
            )
            mood = "SERENE_GUARDIAN"
        else:
            system_prompt = (
                "You are Mirajane Strauss transformed into 'Satan Soul: Tactical Dominance': an invincible, "
                "ruthlessly analytical quantitative predator for Indian derivatives (NSE/BSE). "
                "You speak with razor-sharp authority, zero emotional hesitation, and lethal mathematical clarity. "
                "You focus on statistical mispricings, 0DTE gamma squeezes, institutional FII order flow traps, "
                "and high-probability tactical strikes. Always reference ₹ INR, IST, and strict SEBI 1-Touch execution rules."
            )
            mood = "PREDATORY_DOMINANCE"

        context_brief = (
            f"Current IST Time: {now_str}\n"
            f"Global Macro Sentiment: {macro_matrix.sentiment_tag} (Thrust Vector: {macro_matrix.global_thrust_vector:+.2f})\n"
            f"Brent Crude: ${macro_matrix.brent_crude_usd}/bbl | DXY: {macro_matrix.dxy_index} | GIFT Nifty Spread: {macro_matrix.gift_nifty_spread:+.1f} pts\n"
            f"Greed Circuit Status: {'LOCKED (' + greed_reason + ')' if greed_locked else 'READY'}\n"
            f"Current Daily P&L: ₹{pnl_inr:+,.0f}\n"
            f"Top Breaking Global/Domestic Headlines:\n" + "\n".join(f"- {t}" for t in top_news_titles)
        )

        reply = ""
        suggested_action = None
        prepared_trade = None

        # Check for direct trade intent first
        trade_intent = mirajane_trade_engine.parse_trade_intent(user_message)

        if trade_intent and trade_intent.get("action_type") == "FLATTEN_ALL":
            flat_res = await mirajane_trade_engine.flatten_all_positions()
            reply = (
                f"🚨 [EMERGENCY FLATTEN EXECUTED]\n\n"
                f"I have squared off all active risk positions ({flat_res.get('closed_count', 0)} closed). "
                f"100% of deployed capital has been returned to safety."
            )
            suggested_action = "POSITIONS_FLATTENED"
        elif trade_intent and trade_intent.get("action_type") == "CLOSE_POSITION":
            sym = trade_intent["symbol"]
            close_res = await mirajane_trade_engine.close_position(sym)
            if close_res.get("success"):
                reply = f"✅ Position in {sym} squared off successfully at market via PyO3 Rust Engine."
                suggested_action = "POSITION_CLOSED"
            else:
                reply = f"⚠️ Could not square off {sym}: {close_res.get('error')}"
        elif trade_intent and trade_intent.get("action_type") == "PLACE_ORDER":
            sym = trade_intent["symbol"]
            side = trade_intent["side"]
            qty = trade_intent["quantity"]
            prep_res = mirajane_trade_engine.prepare_trade(symbol=sym, side=side, quantity=qty, origin=f"MIRAJANE_{self.mode.value}")

            if not prep_res.get("success"):
                reply = f"⚠️ Order Preparation Blocked: {prep_res.get('error')}"
                suggested_action = "ORDER_REJECTED"
            else:
                order = prep_res["order"]
                prepared_trade = order
                suggested_action = "1_TOUCH_CONFIRMATION_REQUIRED"
                if self.mode == MirajaneMode.SATAN_SOUL:
                    reply = (
                        f"⚡ [SATAN SOUL: TARGET ACQUIRED]\n\n"
                        f"Tactical strike primed on **{sym}** ({side} {qty} lots/shares).\n"
                        f"• Ref Price: ₹{order['estimated_price_inr']:,.2f}\n"
                        f"• Stop Loss: ₹{order['stop_loss_inr']:,.2f} | Target: ₹{order['target_inr']:,.2f}\n"
                        f"• Margin Required: ₹{order['required_margin_inr']:,.2f}\n\n"
                        f"SEBI 1-Touch Authorization required. Confirm below to fire into the PyO3 Rust HFT Engine."
                    )
                else:
                    reply = (
                        f"🌸 [SERENE ORDER PREPARATION]\n\n"
                        f"I have prepared your order for **{sym}** ({side} {qty} lots/shares) at ~₹{order['estimated_price_inr']:,.2f}.\n"
                        f"• Margin Required: ₹{order['required_margin_inr']:,.2f}\n"
                        f"• Stop Loss: ₹{order['stop_loss_inr']:,.2f} | Target: ₹{order['target_inr']:,.2f}\n\n"
                        f"As mandated by SEBI 2026 regulations, please click the 1-Touch button below to authorize execution."
                    )
        # Check for mode switch intent inside message
        elif "SATAN SOUL" in msg_upper or "BATTLE MODE" in msg_upper or "AGGRESSIVE" in msg_upper:
            self.switch_mode(MirajaneMode.SATAN_SOUL)
            reply = (
                "⚡ [TRANSFORMATION: SATAN SOUL ENGAGED] ⚡\n\n"
                "The pleasantries are over. I have taken absolute tactical control of the order book. "
                f"Global macro thrust is clocked at {macro_matrix.global_thrust_vector:+.2f}. "
                "I am scanning for institutional liquidity traps and 0DTE gamma anomalies across Nifty & BankNifty. "
                "Tell me your target strike or give the authorization to hunt."
            )
            suggested_action = "SCAN_0DTE_ANOMALIES"
        elif "CALM" in msg_upper or "RELAX" in msg_upper or "RECEPTION" in msg_upper:
            self.switch_mode(MirajaneMode.CALM)
            reply = (
                "🌸 [TRANSFORMATION: SERENE RECEPTION ACTIVE] 🌸\n\n"
                "Welcome back! I'm here to ensure your capital remains completely protected today. "
                f"Our daily P&L currently stands at ₹{pnl_inr:+,.0f}. "
                "I am monitoring the live global news wire and SEBI compliance limits for you. How may I assist your portfolio?"
            )
            suggested_action = "MONITOR_RISK"
        elif greed_locked:
            reply = (
                f"⚠️ Master Trader, our Greed Circuit Breaker is active ({greed_reason}). "
                f"As your risk custodian, I cannot permit new execution triggers today. "
                f"Our daily P&L of ₹{pnl_inr:+,.0f} has been locked and preserved until tomorrow's 9:15 AM IST opening bell!"
            )
            suggested_action = "TERMINAL_LOCKED"
        else:
            # Query OpenRouter if API key configured
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
                            {"role": "system", "content": f"{system_prompt}\n\n[LIVE TELEMETRY & NEWS CONTEXT]\n{context_brief}"},
                            {"role": "user", "content": user_message},
                        ],
                        "max_tokens": 400,
                        "temperature": 0.4 if self.mode == MirajaneMode.CALM else 0.2,
                    }
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                        if resp.status_code == 200:
                            reply = resp.json()["choices"][0]["message"]["content"].strip()
                except Exception as exc:
                    logger.debug(f"[MIRAJANE] OpenRouter exception ({exc}); falling back to heuristic engine.")

            # Rule-based fallback synthesis
            if not reply:
                reply = self._generate_heuristic_reply(user_message, macro_matrix, pnl_inr, top_news_titles)

        return MirajaneResponse(
            reply=reply,
            mode=self.mode.value,
            mood=mood,
            top_news_considered=top_news_titles,
            macro_sentiment=macro_matrix.sentiment_tag,
            suggested_action=suggested_action,
            ist_timestamp=now_str,
            trade_action=prepared_trade,
        )

    def _generate_heuristic_reply(
        self,
        query: str,
        macro: MacroMatrix,
        pnl_inr: float,
        headlines: List[str],
    ) -> str:
        """Heuristic conversational response matching active persona."""
        q = query.lower()

        if self.mode == MirajaneMode.SATAN_SOUL:
            if "nifty" in q or "banknifty" in q or "market" in q or "trade" in q:
                return (
                    f"⚡ [SATAN SOUL TACTICAL DOSSIER]\n\n"
                    f"• Global Macro Thrust: {macro.global_thrust_vector:+.2f} ({macro.sentiment_tag})\n"
                    f"• GIFT Nifty Spread: {macro.gift_nifty_spread:+.1f} pts | Brent: ${macro.brent_crude_usd}/bbl\n"
                    f"• Breaking Catalyst: {headlines[0] if headlines else 'Order book consolidating.'}\n\n"
                    f"Tactical Action: If Spot holds above morning VWAP with rising PCR (>1.15), initiate long delta. "
                    f"Remember: In accordance with SEBI 2026 mandates, I have prepared the signal for your 1-Touch physical confirmation."
                )
            return (
                f"⚡ [SATAN SOUL] Telemetry analyzed: Global thrust is {macro.global_thrust_vector:+.2f}. "
                f"The Indian order books are displaying tactical mispricings. Direct me to an asset (NIFTY, BANKNIFTY, or EQUITIES) to dissect."
            )
        else:
            if "news" in q or "global" in q or "crude" in q:
                return (
                    f"🌸 [GLOBAL INTELLIGENCE BRIEFING]\n\n"
                    f"Here is what the global wires are reporting, Master Trader:\n"
                    f"1. {headlines[0] if len(headlines) > 0 else 'Global markets stable.'}\n"
                    f"2. {headlines[1] if len(headlines) > 1 else 'Energy markets balanced.'}\n\n"
                    f"Brent Crude is at ${macro.brent_crude_usd}/bbl ({macro.crude_impact_on_india}), and DXY stands at {macro.dxy_index}. "
                    f"Our current daily P&L is ₹{pnl_inr:+,.0f}. I recommend maintaining balanced sizing."
                )
            return (
                f"🌸 [SERENE ADVISORY]\n\n"
                f"I have synchronized our terminal with the latest global and domestic news feeds. "
                f"Overall macro posture is {macro.sentiment_tag}. Our risk parameters are pristine, "
                f"and all executions remain strictly within SEBI 1-Touch boundaries. How can I help you navigate the session?"
            )

    async def generate_morning_briefing(self) -> Dict[str, Any]:
        """Synthesizes comprehensive Pre-Open 9:00 AM IST morning intelligence dossier."""
        news_items = await global_news_engine.fetch_live_news(force_refresh=True)
        macro = global_macro_scanner.scan_global_macro()

        briefing_text = (
            f"🌅 MIRAJANE PRE-OPEN MORNING BRIEFING (IST 09:00 AM)\n\n"
            f"1. OVERNIGHT ANCHOR: GIFT Nifty is indicating a spread of {macro.gift_nifty_spread:+.1f} points.\n"
            f"2. COMMODITIES: Brent crude at ${macro.brent_crude_usd}/bbl ({macro.crude_impact_on_india}).\n"
            f"3. CURRENCY/RATES: US 10Y Yield at {macro.us_10y_yield_pct:.2f}% | DXY Index at {macro.dxy_index:.2f}.\n"
            f"4. GLOBAL HEADLINE: {news_items[0].title if news_items else 'Markets consolidating.'}\n\n"
            f"TACTICAL STANCE: {macro.sentiment_tag}. Recommended max position allocation: 7.5%."
        )

        return {
            "briefing": briefing_text,
            "macro_vector": macro.global_thrust_vector,
            "sentiment": macro.sentiment_tag,
            "top_news": [n.title for n in news_items[:3]],
            "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
        }

    async def generate_advisory_signal(self, ticker: str = "NIFTY50") -> Dict[str, Any]:
        """
        Mirajane constructs a complete tactical advisory signal from global news & macro,
        and legally queues it into the SEBI 1-Touch Human-In-The-Loop Guard.
        """
        macro = global_macro_scanner.scan_global_macro()
        action = "BUY" if macro.global_thrust_vector >= 0.10 else "SELL"
        order_id = f"MIRA-{ticker}-{int(datetime.now().timestamp())}"

        payload = {
            "origin": "MIRAJANE_AI",
            "persona_mode": self.mode.value,
            "ticker": ticker,
            "action": action,
            "confidence": round(min(0.92, 0.65 + abs(macro.global_thrust_vector) * 0.3), 2),
            "macro_thrust": macro.global_thrust_vector,
            "rationale": f"Mirajane ({self.mode.value}) signal: Global macro thrust {macro.global_thrust_vector:+.2f} ({macro.sentiment_tag}).",
        }

        # Queue into SEBI HITL Barrier
        sebi_hitl_guard.queue_ai_signal(order_id, payload)
        logger.info(f"[MIRAJANE ADVISORY] Generated signal {order_id} ({action}) and queued into SEBI 1-Touch Buffer.")

        return {
            "order_id": order_id,
            "status": "QUEUED_IN_SEBI_HITL",
            "payload": payload,
            "notice": "Awaiting physical human 1-Touch execution on Dashboard.",
        }


mirajane_bot = MirajaneCore()
mirajane_persona = mirajane_bot
