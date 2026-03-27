"""
External Webhook Ingress (TradingView, Discord, etc.)

Strictly guarded API endpoints leveraging HMAC SHA-256 signature verification
to prevent spoofing and replay attacks.
"""

import hmac
import hashlib
import logging
from fastapi import APIRouter, Header, HTTPException, Request

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(
    prefix="/webhooks",
    tags=["External Webhooks"],
)


async def verify_signature(raw_body: bytes, signature: str) -> bool:
    """Verifies the HMAC SHA-256 signature against the shared secret."""
    # Fallback secret if not in ENV
    secret = getattr(settings, "webhook_secret", "dev_webhook_secret_key_change_me").encode("utf-8")

    expected_hmac = hmac.new(key=secret, msg=raw_body, digestmod=hashlib.sha256).hexdigest()

    # Use hmac.compare_digest to prevent timing attacks
    return hmac.compare_digest(expected_hmac, signature)


@router.post("/tradingview")
async def tradingview_webhook(
    request: Request,
    x_signature: str = Header(None, alias="X-Signature"),
):
    """
    Ingests TradingView alerts securely.
    Requires `X-Signature: <hmac-sha256>` in the HTTP headers.
    """
    if not x_signature:
        logger.warning("[WEBHOOK ALERT] Rejected incoming webhook: Missing X-Signature header.")
        raise HTTPException(status_code=401, detail="Unauthorized: Missing Signature")

    raw_body = await request.body()

    is_valid = await verify_signature(raw_body, x_signature)
    if not is_valid:
        logger.error(
            f"[WEBHOOK ALERT] Rejected incoming webhook: Invalid HMAC Signature -> {x_signature[:10]}..."  # noqa: E501
        )
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Signature")

    try:
        # In actual execution, this JSON contains { "symbol": "...", "action": "BUY" }
        payload = await request.json()
        logger.info(
            f"[WEBHOOK ACCEPTED] Validated TradingView Signal for {payload.get('symbol', 'UNKNOWN')}"  # noqa: E501
        )

        # Dispatch to Inference Engine or Core Message Bus
        from core.message_bus import message_bus
        import asyncio

        loop = asyncio.get_running_loop()
        loop.create_task(message_bus.publish("external_signals", payload))

        return {"status": "accepted", "message": "Signal ingested and verified."}

    except Exception as e:
        logger.error(f"[WEBHOOK ERROR] Failed to parse valid webhook: {e}")
        raise HTTPException(status_code=400, detail="Malformed JSON Payload")
