"""
Mirajane Voice Agent Engine (NVIDIA Nemotron Voice Blueprint Architecture).
Provides real-time verbal interaction for Mirajane Strauss:
- Speech-to-Intent transcription & parsing.
- Dual-mode Voice Prosody & Audio Configuration:
    - CALM: Serene, warm, reassuring cadence (Pitch: 1.15, Rate: 1.0, Volume: 0.95).
    - SATAN_SOUL: Tactical, razor-sharp, assertive cadence (Pitch: 0.85, Rate: 1.25, Volume: 1.0).
- Verbal trade confirmation and SEBI HITL 1-Touch ticket generation.
"""

import re
from typing import Dict, Any, Optional
from ai_agent.mirajane.persona import mirajane_persona
from ai_agent.mirajane.trading_engine import mirajane_trade_engine


class MirajaneVoiceAgent:
    """
    Voice Intercom engine converting verbal trader commands into conversational
    intelligence, audio synthesis prosody parameters, and 1-Touch SEBI trade tickets.
    """

    def __init__(self):
        self.bot_name = "Mirajane Strauss"

    def get_speech_config(self, mode: str = "CALM") -> Dict[str, Any]:
        """
        Returns Web Speech API synthesis configuration matched to Mirajane's active persona.
        Strictly enforces natural female pitch and tone.
        """
        if mode == "SATAN_SOUL":
            return {
                "preferred_voices": [
                    "Microsoft Heera - English (India)",
                    "Microsoft Zira - English (United States)",
                    "Microsoft Hazel - English (United Kingdom)",
                    "Microsoft Susan - English (United Kingdom)",
                    "Google UK English Female",
                    "Google US English Female",
                ],
                "pitch": 1.12,  # Assertive, crisp female tone
                "rate": 1.08,   # Direct, focused execution cadence
                "volume": 1.0,
                "accent": "en-IN",
                "sound_effect": "tactical_activation.wav",
                "persona_tag": "ALPHA_TACTICAL_FEMALE",
            }
        else:
            return {
                "preferred_voices": [
                    "Microsoft Heera - English (India)",
                    "Microsoft Zira - English (United States)",
                    "Microsoft Hazel - English (United Kingdom)",
                    "Microsoft Susan - English (United Kingdom)",
                    "Google US English Female",
                    "Google UK English Female",
                ],
                "pitch": 1.22,  # Melodious, articulate female tone
                "rate": 1.02,   # Measured, clear cadence
                "volume": 1.0,
                "accent": "en-IN",
                "sound_effect": "serene_chime.wav",
                "persona_tag": "RISK_CUSTODIAN_FEMALE",
            }

    async def process_voice_command(
        self,
        transcript: str,
        user_jwt: str = "DEV_SESSION_SEBI_HITL",
    ) -> Dict[str, Any]:
        """
        Processes incoming voice transcript from user.
        Dispatches to Mirajane persona and checks if a trade action was verbally requested.
        """
        cleaned_text = transcript.strip()
        active_mode = mirajane_persona.mode

        # 1. Generate conversational response via MirajaneCore
        res_obj = await mirajane_persona.chat(cleaned_text, portfolio_context={"user_jwt": user_jwt})
        chat_reply = res_obj.to_dict()

        # 2. Extract Speech Synthesis Prosody Config
        active_mode_str = mirajane_persona.mode.value if hasattr(mirajane_persona.mode, "value") else str(mirajane_persona.mode)
        speech_config = self.get_speech_config(active_mode_str)

        # 3. Create clean speech text (stripping markdown tables/code blocks for speech clarity)
        speech_text = self._sanitize_for_speech(chat_reply.get("reply", ""))

        return {
            "transcript_heard": cleaned_text,
            "bot_mode": active_mode_str,
            "spoken_response": speech_text,
            "full_markdown_reply": chat_reply.get("reply", ""),
            "speech_config": speech_config,
            "trade_action": chat_reply.get("trade_action"),
            "sebi_hitl_ticket": chat_reply.get("trade_action", {}).get("order_id") if chat_reply.get("trade_action") else None,
            "status": "PROCESSED",
        }

    def _sanitize_for_speech(self, text: str) -> str:
        """Strips Markdown symbols, JSON code blocks, emojis, and URLs for natural vocalization."""
        # Remove code blocks
        clean = re.sub(r"```[\s\S]*?```", " [Details generated on screen] ", text)
        # Remove emojis and high surrogate characters
        clean = re.sub(r"[\U00010000-\U0010ffff]", "", clean)
        # Remove markdown headers, bullets and asterisks
        clean = re.sub(r"[#*`_~|>-]", " ", clean)
        # Normalize INR symbols to 'Rupees'
        clean = clean.replace("₹", "Rupees ")
        # Trim multiple spaces
        clean = " ".join(clean.split())
        # Truncate if excessively long for speech
        if len(clean) > 400:
            clean = clean[:380] + "... Full breakdown displayed on terminal."
        return clean


mirajane_voice_agent = MirajaneVoiceAgent()
