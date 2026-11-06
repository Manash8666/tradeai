import hmac
import hashlib
import json
import logging
import zoneinfo
from datetime import datetime
from typing import Optional, Tuple
from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field

from backend.app.core.sebi_hitl_compliance import sebi_hitl_guard

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")

router = APIRouter(prefix="/integrations/tradingview", tags=["TradingView Bridge"])


class TradingViewWebhookPayload(BaseModel):
    ticker: str = Field(..., example="NSE:NIFTY50")
    action: str = Field(..., example="BUY")  # "BUY", "SELL", "CLOSE"
    price: float = Field(..., example=24520.5)
    volume: Optional[float] = Field(default=None, example=50000.0)
    timeframe: str = Field(default="5m", example="5m")
    strategy_name: str = Field(default="PineScriptStrategy", example="SuperTrend-RSI-V3")
    alert_message: Optional[str] = Field(default=None, example="Long Entry condition met")
    webhook_secret: str = Field(default="", example="tv_secret_token_123")


class NormalizedSignal(BaseModel):
    source: str = "TRADINGVIEW"
    ticker: str
    exchange: str  # "NSE" or "BSE"
    action: str
    price_inr: float
    timeframe: str
    ist_timestamp: str
    strategy_name: str
    signal_hash: str
    sebi_hitl_required: bool = True  # MANDATORY SEBI 2026: External webhook signals MUST pass human approval


class TradingViewBridge:
    """
    Bi-Directional Gateway between TradingView Pine Script alerts and the Indian HFT Core.
    Normalizes symbols, computes SHA-256 cryptographic audit digests,
    and automatically routes triggers into the SEBI 1-Touch Human-In-The-Loop Buffer.
    """

    def __init__(self, secret_token: str = "tv_default_secret"):
        self.secret_token = secret_token

    def normalize_ticker(self, tv_ticker: str) -> Tuple[str, str]:
        """
        Translates TradingView prefix syntax (e.g. 'NSE:NIFTY50', 'BSE:SENSEX')
        into normalized native Indian exchange symbols.
        """
        clean = tv_ticker.strip().upper()
        if ":" in clean:
            prefix, symbol = clean.split(":", 1)
            exchange = "BSE" if "BSE" in prefix else "NSE"
            return symbol, exchange
        return clean, "NSE"

    def generate_signal_hash(self, payload_dict: dict) -> str:
        """Computes SHA-256 fingerprint for SEBI 5-year audit trail."""
        serialized = json.dumps(payload_dict, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def normalize_to_signal(self, payload: TradingViewWebhookPayload) -> NormalizedSignal:
        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        symbol, exchange = self.normalize_ticker(payload.ticker)
        action = payload.action.upper().strip()

        raw_data = {
            "ticker": symbol,
            "exchange": exchange,
            "action": action,
            "price": payload.price,
            "timeframe": payload.timeframe,
            "strategy": payload.strategy_name,
            "timestamp": now_str,
        }
        sig_hash = self.generate_signal_hash(raw_data)

        signal = NormalizedSignal(
            source="TRADINGVIEW",
            ticker=symbol,
            exchange=exchange,
            action=action,
            price_inr=round(payload.price, 2),
            timeframe=payload.timeframe,
            ist_timestamp=now_str,
            strategy_name=payload.strategy_name,
            signal_hash=sig_hash,
            sebi_hitl_required=True,
        )

        return signal

    def route_to_sebi_hitl(self, signal: NormalizedSignal) -> str:
        """
        SEBI APRIL 2026 MANDATE ENFORCEMENT:
        No external alert can bypass the physical human trigger.
        Enqueues signal into SEBIHumanInTheLoopGuard with 4000ms expiration bounds.
        """
        order_id = f"TV-{signal.ticker}-{signal.signal_hash[:8]}"
        payload = signal.model_dump()
        sebi_hitl_guard.queue_ai_signal(order_id, payload)
        logger.warning(
            f"[TRADINGVIEW BRIDGE] External alert {order_id} intercepted & enqueued. "
            f"Awaiting physical 1-Touch authorization on React Terminal."
        )
        return order_id


tv_bridge = TradingViewBridge()


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_tradingview_alert(payload: TradingViewWebhookPayload):
    """
    Receives incoming alerts from TradingView Pine Script webhooks.
    Normalizes the payload and pushes it into the SEBI 1-Touch Execution barrier.
    """
    try:
        signal = tv_bridge.normalize_to_signal(payload)
        order_id = tv_bridge.route_to_sebi_hitl(signal)

        return {
            "status": "QUEUED_FOR_HUMAN_AUTH",
            "order_id": order_id,
            "signal": signal.model_dump(),
            "sebi_notice": "Alert accepted as ADVISORY SIGNAL. Awaiting physical trader 1-Touch click.",
        }
    except Exception as exc:
        logger.error(f"[TRADINGVIEW BRIDGE] Webhook ingestion failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {exc}",
        )
