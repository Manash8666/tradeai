"""
Mirajane Strauss — Autonomous Global Intelligence & Quantitative Trading Bot.
Connects the Indian Trading Platform to real-time global news, macro feeds, and tactical execution.
"""
from .persona import MirajaneCore, MirajaneMode, MirajaneResponse, mirajane_bot
from .news_engine import GlobalNewsEngine, NewsItem, global_news_engine
from .macro_scanner import GlobalMacroScanner, MacroMatrix, global_macro_scanner
from .bot_router import router as mirajane_router

__all__ = [
    "MirajaneCore",
    "MirajaneMode",
    "MirajaneResponse",
    "mirajane_bot",
    "GlobalNewsEngine",
    "NewsItem",
    "global_news_engine",
    "GlobalMacroScanner",
    "MacroMatrix",
    "global_macro_scanner",
    "mirajane_router",
]
