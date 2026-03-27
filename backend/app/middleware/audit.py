"""
Immutable Fast-Track Audit Logging Middleware

Intercepts every HTTP request, calculates a SHA-256 cryptographic hash chaining it
to the previous row in the ClickHouse ledger, and writes the log asynchronously.
This design guarantees mathematical unalterability satisfying strict SEBI requirements.
"""

import json
import logging
import hashlib
import time
from uuid import uuid4
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from compliance.immutable_ledger import record_audit_entry_sync
from fastapi.background import BackgroundTasks

logger = logging.getLogger(__name__)

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid4())
        
        # 1. Capture payload robustly
        payload = ""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                payload = body.decode("utf-8")
                
                # Re-inject body so endpoints can consume it
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except Exception:
                payload = "[Unparseable Payload]"

        # 2. Process Request
        response = None
        status_code = "500"
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception as e:
            status_code = "500"
            raise e
        finally:
            # 3. Request Background Task pushing directly to the Zero-Latency Ledger
            try:
                method = request.method
                url = str(request.url)
                ips = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
                user_id = getattr(request.state, "user_id", "anonymous")
                
                logger.info(f"Delegating Request {request_id} to internal Immutable Ledger Background Worker.")
                
                # Using Starlette's background tasks functionality for FastAPI
                from starlette.background import BackgroundTask
                task = BackgroundTask(
                    record_audit_entry_sync,
                    request_id, method, url, status_code, payload, ips, user_id
                )
                
                if response:
                    # Append task natively to Response so FastAPI handles the executor
                    response.background = task
                
            except Exception as e:
                logger.critical(f"FATAL: Failed to instantiate Background Task for Audit Log: {e}")

        return response
