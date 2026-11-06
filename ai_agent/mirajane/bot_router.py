import math
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .persona import mirajane_bot, MirajaneMode
from .news_engine import global_news_engine
from .macro_scanner import global_macro_scanner
from .trading_engine import mirajane_trade_engine
from .voice_agent import mirajane_voice_agent
from .human_behavior_engine import human_behavior_engine
from .evolution_engine import mirajane_evolution_engine
from .previral_news_radar import previral_news_radar
from backend.app.trading.market_data_service import market_data_service
from ai_agent.models.moe_quant_router import moe_quant_router
from ai_agent.models.strategy_synthesizer import strategy_synthesizer
from backend.app.trading.stock_recommender import stock_recommender
from backend.app.trading.fast_iv_solver import fast_implied_volatility

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mirajane", tags=["Mirajane AI Bot"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str = Field(..., description="Trader query or instruction to Mirajane.")
    daily_pnl_inr: Optional[float] = Field(default=0.0, description="Current daily P&L in INR.")


class ModeSwitchRequest(BaseModel):
    mode: str = Field(..., description="'CALM' (Serene Reception) or 'SATAN_SOUL' (Tactical Dominance)")


class AdvisoryRequest(BaseModel):
    ticker: str = Field(default="NIFTY50", description="Target NSE/BSE ticker.")


class ExecuteOrderRequest(BaseModel):
    order_id: str = Field(..., description="Prepared Mirajane order ID.")
    human_jwt: Optional[str] = Field(default="DEV_SESSION_JWT", description="SEBI 2026 Mandated Human Authorization Token.")


class ClosePositionRequest(BaseModel):
    symbol: str = Field(..., description="Symbol to square off.")


class VoiceChatRequest(BaseModel):
    transcript: str = Field(..., description="Verbal speech transcript from trader.")
    human_jwt: Optional[str] = Field(default="DEV_SESSION_SEBI_HITL")


class SynthesizeStrategyRequest(BaseModel):
    strategy_type: str = Field(default="VOLATILITY_ARBITRAGE", description="VOLATILITY_ARBITRAGE, MOMENTUM_BREAKOUT, or MEAN_REVERSION")
    symbol: str = Field(default="NIFTY", description="Target NSE underlying")


class EvaluateDailyRequest(BaseModel):
    final_pnl_inr: float = Field(..., description="Final realized P&L for the session in INR.")
    session_summary: Optional[str] = Field(default="Standard session close", description="Session review context.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status", summary="Mirajane Bot Status & Macro Telemetry")
async def get_status() -> Dict[str, Any]:
    """Retrieves current persona mode, global macro vector, and news counts."""
    macro = global_macro_scanner.scan_global_macro()
    sentiment = global_news_engine.get_market_sentiment_summary()

    return {
        "bot_name": "Mirajane Strauss",
        "active_mode": mirajane_bot.mode.value,
        "mode_description": "Serene Reception (Risk Custodian)" if mirajane_bot.mode == MirajaneMode.CALM else "Satan Soul (Tactical Alpha Hunter)",
        "global_macro_thrust": macro.global_thrust_vector,
        "sentiment_tag": macro.sentiment_tag,
        "brent_crude_usd": macro.brent_crude_usd,
        "gift_nifty_spread": macro.gift_nifty_spread,
        "dxy_index": macro.dxy_index,
        "total_global_news_cached": sentiment.get("total_news", 0),
        "regulatory_alerts_active": sentiment.get("regulatory_alerts", 0),
    }


@router.post("/mode", summary="Switch Mirajane Persona Mode")
async def switch_mode(payload: ModeSwitchRequest) -> Dict[str, Any]:
    """Toggles Mirajane between Serene Reception and Satan Soul."""
    new_mode = mirajane_bot.switch_mode(payload.mode)
    return {
        "status": "MODE_SWITCHED",
        "active_mode": new_mode.value,
        "message": f"Mirajane transformed into {new_mode.value}!",
    }


@router.post("/chat", summary="Chat with Mirajane")
async def chat_with_mirajane(payload: ChatRequest) -> Dict[str, Any]:
    """Sends a query to Mirajane with live internet news & macro grounding."""
    try:
        portfolio_context = {"daily_pnl_inr": payload.daily_pnl_inr}
        res = await mirajane_bot.chat(payload.message, portfolio_context=portfolio_context)
        return res.to_dict()
    except Exception as exc:
        logger.error(f"[MIRAJANE CHAT] Error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mirajane reasoning engine error: {exc}",
        )


@router.get("/news", summary="Live Global Financial News Feed")
async def get_live_news() -> List[Dict[str, Any]]:
    """Streams top real-time global and domestic financial news items."""
    news = await global_news_engine.fetch_live_news()
    return [item.to_dict() for item in news]


@router.post("/scan", summary="Force-Refresh Global Internet Scan")
async def force_scan_news() -> Dict[str, Any]:
    """Force re-fetches live internet RSS feeds from global macro sources."""
    news = await global_news_engine.fetch_live_news(force_refresh=True)
    macro = global_macro_scanner.scan_global_macro()
    return {
        "status": "SCAN_COMPLETE",
        "items_ingested": len(news),
        "macro_thrust": macro.global_thrust_vector,
        "sentiment_tag": macro.sentiment_tag,
    }


@router.get("/briefing", summary="Pre-Open Morning Briefing")
async def get_morning_briefing() -> Dict[str, Any]:
    """Generates comprehensive pre-market global intelligence summary."""
    return await mirajane_bot.generate_morning_briefing()


@router.post("/advisory", summary="Generate SEBI-Compliant Advisory Signal")
async def generate_advisory(payload: AdvisoryRequest) -> Dict[str, Any]:
    """Mirajane generates a tactical signal and queues it to the 1-Touch HITL barrier."""
    return await mirajane_bot.generate_advisory_signal(payload.ticker)


@router.post("/trade/execute", summary="Execute Prepared Order via Rust HFT OMS")
async def execute_trade(payload: ExecuteOrderRequest) -> Dict[str, Any]:
    """
    Executes a Mirajane-prepared order through the PyO3 Rust HFT Engine
    upon physical 1-Touch human confirmation.
    """
    res = await mirajane_trade_engine.execute_trade(payload.order_id, human_jwt=payload.human_jwt or "DEV_JWT")
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("error"))
    return res


@router.get("/trade/positions", summary="Active Mirajane Positions")
async def get_active_positions() -> List[Dict[str, Any]]:
    """Returns all open positions actively managed by Mirajane."""
    return mirajane_trade_engine.get_open_positions()


@router.post("/trade/close", summary="Square Off Active Position")
async def close_position(payload: ClosePositionRequest) -> Dict[str, Any]:
    """Squares off a specific position through the execution engine."""
    res = await mirajane_trade_engine.close_position(payload.symbol)
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("error"))
    return res


@router.post("/trade/flatten", summary="Emergency Flatten All Positions")
async def flatten_all_positions() -> Dict[str, Any]:
    """Emergency master square off: flattens 100% of open positions immediately."""
    return await mirajane_trade_engine.flatten_all_positions()


# ---------------------------------------------------------------------------
# Phase 21: Voice Agent, MoE Reasoning & Strategy Synthesis Endpoints
# ---------------------------------------------------------------------------


@router.post("/voice/chat", summary="Mirajane Voice Intercom (Nemotron Blueprint)")
async def voice_chat(payload: VoiceChatRequest) -> Dict[str, Any]:
    """Processes spoken verbal instructions and returns audio synthesis parameters."""
    return await mirajane_voice_agent.process_voice_command(
        transcript=payload.transcript,
        user_jwt=payload.human_jwt or "DEV_SESSION_SEBI_HITL",
    )


@router.get("/voice/config", summary="Mirajane Voice Prosody Configuration")
async def get_voice_config() -> Dict[str, Any]:
    """Returns speech synthesis pitch, rate, and voice profile matching active mode."""
    return mirajane_voice_agent.get_speech_config(mirajane_bot.mode.value)


@router.get("/moe/infer", summary="DeepSeek-V3 Mixture-of-Experts Alpha Directive")
async def get_moe_inference() -> Dict[str, Any]:
    """
    Runs DeepSeek-V3 inspired Mixture-of-Experts routing across:
    MacroRegime, DerivativesGreek, PriceActionSMC, and ExecutionRisk experts.
    """
    macro = global_macro_scanner.scan_global_macro()
    market_snapshot = {
        "brent_crude_usd": macro.brent_crude_usd,
        "gift_nifty_spread": macro.gift_nifty_spread,
        "dxy_index": macro.dxy_index,
        "atm_iv": 15.81,
        "pcr": 1.05,
        "volatility_skew": 0.015,
        "bull_fvgs_count": 3,
        "bear_fvgs_count": 1,
        "bos_bullish_count": 4,
        "margin_used_pct": 14.5,
        "greed_locked": False,
        "daily_loss_pct": 0.0,
    }
    return moe_quant_router.route_and_infer(market_snapshot)


@router.post("/strategy/synthesize", summary="DeepSeek-Coder Strategy Synthesizer with DSR Verification")
async def synthesize_strategy(payload: SynthesizeStrategyRequest) -> Dict[str, Any]:
    """
    Autonomously creates, backtests, and statistically verifies (Bailey & López de Prado DSR)
    a new quantitative option strategy against 5-year historical Bhavcopy data.
    """
    return strategy_synthesizer.synthesize_candidate_strategy(
        strategy_type=payload.strategy_type,
        target_symbol=payload.symbol,
    )


@router.get("/predict", summary="Multi-Horizon Technical Stock Recommender")
async def get_stock_prediction(symbol: str = "NIFTY") -> Dict[str, Any]:
    """
    Computes multi-horizon probabilistic forecasts (15m scalp, 1h intraday, EOD)
    with ATR targets and stop-loss levels in ₹ INR.
    """
    sym = symbol.upper()
    spot = 23806.95 if sym == "NIFTY" else 51240.20
    # Simulate recent 35 candles
    candles = [
        {
            "close": spot + math.sin(i * 0.4) * 35.0,
            "high": spot + math.sin(i * 0.4) * 35.0 + 8.0,
            "low": spot + math.sin(i * 0.4) * 35.0 - 8.0,
            "open": spot + math.sin(i * 0.4) * 35.0 - 2.0,
        }
        for i in range(35)
    ]
    return stock_recommender.generate_multi_horizon_prediction(sym, spot, candles)


@router.get("/sentience/behavior", summary="Sentient Human Behavior & Market Psychology Flow")
async def get_human_behavior(symbol: str = "NIFTY") -> Dict[str, Any]:
    """
    Decodes market mechanics as human psychology: FOMO/Panic scores, retail traps,
    FII/DII operator divergence, and Mirajane's authentic sentient voice reflection.
    """
    sym = symbol.upper()
    spot = 23806.95 if sym == "NIFTY" else 51240.20
    return human_behavior_engine.analyze_market_human_flow(symbol=sym, spot=spot, vix=15.81)


@router.get("/evolution/status", summary="Mirajane Darwinian Evolution & Survival Telemetry")
async def get_evolution_status() -> Dict[str, Any]:
    """
    Returns current champion generation, daily stipulated mandate (₹2,00,000 / ₹25k target),
    survival streak, and replacement post-mortem history.
    """
    return mirajane_evolution_engine.get_status()


@router.post("/evolution/execute_daily", summary="Dispatches Mirajane's Daily Stipulated Autonomous Trade")
async def execute_daily_evolution_trade() -> Dict[str, Any]:
    """
    Synthesizes and prepares Mirajane's mandatory high-conviction daily strategy trade.
    """
    return mirajane_evolution_engine.generate_autonomous_daily_trade(spot=23806.95)


@router.post("/evolution/evaluate", summary="Darwinian Session Evaluation (Survival or Replacement)")
async def evaluate_daily_session(payload: EvaluateDailyRequest) -> Dict[str, Any]:
    """
    Evaluates session profitability against mandate:
    - If P&L > 0: Mirajane survives and model weights reinforce.
    - If P&L <= 0: Mirajane is eliminated, failure post-mortem logged, hyperparameters mutate,
      and a next-generation champion is spawned.
    """
    return mirajane_evolution_engine.evaluate_daily_performance(
        final_daily_pnl_inr=payload.final_pnl_inr,
        session_summary=payload.session_summary or "Session close review",
    )


@router.get("/previral/news", summary="Pre-Viral Upstream Overseas News Radar")
async def get_previral_news() -> List[Dict[str, Any]]:
    """
    Scans overseas geopolitical and central banking wires before mainstream Indian media
    or retail channels report them, calculating Dalal Street transmission lag.
    """
    return previral_news_radar.get_previral_radar_feed()


@router.get("/predictions/multi_horizon", summary="Predictive Quarterly, Half-Yearly & Annual Trend Analysis")
async def get_multi_horizon_predictions(symbol: str = "NIFTY") -> Dict[str, Any]:
    """
    Generates institutional projections across 24h, Quarterly (90d), Half-Yearly (180d),
    and Annual (365d) timelines for stocks and indices.
    """
    return previral_news_radar.get_multi_horizon_projections(symbol=symbol)


@router.get("/market/horizons", summary="15 Supported Historical Lookback Horizons")
async def get_market_horizons() -> List[Dict[str, Any]]:
    """
    Lists all 15 supported lookback horizons:
    1h, 3h, 6h, 12h, 24h, 48h, 72h, 10d, 15d, 30d, 45d, 60d, 90d, 180d, 365d.
    """
    return market_data_service.get_supported_horizons()


@router.get("/market/candles", summary="Multi-Horizon Historical OHLCV Series")
async def get_market_candles(
    symbol: str = "NIFTY",
    horizon: str = "24h",
) -> Dict[str, Any]:
    """
    Returns realistic multi-horizon candles for any stock, future, or commodity
    calibrated to the exact November 2026 timeline.
    """
    return await market_data_service.get_historical_candles_async(symbol=symbol, horizon=horizon)


@router.get("/market/premarket", summary="Daily 09:00 IST Morning Pre-Market Sync")
async def get_premarket_cues() -> Dict[str, Any]:
    """
    Fetches overnight global cues, GIFT Nifty opening projection, and Dalal Street stance.
    """
    return market_data_service.get_morning_premarket_cues()

