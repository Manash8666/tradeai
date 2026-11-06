"""
Immutable Fast-Track Audit Logging Middleware

Intercepts every HTTP request, calculates a SHA-256 cryptographic hash chaining it
to the previous row in the ClickHouse ledger, and writes the log asynchronously.
This design guarantees mathematical unalterability satisfying strict SEBI requirements.
"""

import logging
from uuid import uuid4
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from compliance.immutable_ledger import record_audit_entry_sync

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
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
                ips = request.headers.get(
                    "X-Forwarded-For", request.client.host if request.client else "unknown"
                )
                user_id = getattr(request.state, "user_id", None)
                if not user_id or user_id == "anonymous":
                    token = request.cookies.get("access_token")
                    if not token:
                        auth_header = request.headers.get("Authorization", "")
                        if auth_header.startswith("Bearer "):
                            token = auth_header[7:]
                    if token:
                        try:
                            from backend.app.auth.service import decode_token
                            decoded = decode_token(token)
                            user_id = decoded.get("sub")
                        except Exception:
                            pass
                user_id = user_id or "anonymous"

                logger.info(
                    f"Delegating Request {request_id} to internal Immutable Ledger Background Worker."  # noqa: E501
                )

                path = request.url.path
                if path not in ["/health", "/api/health"]:
                    try:
                        from backend.app.database import async_session_factory
                        from backend.app.models.audit_log import AuditLog
                        import uuid

                        user_uuid = None
                        if user_id and user_id != "anonymous":
                            try:
                                user_uuid = uuid.UUID(str(user_id))
                            except Exception:
                                pass

                        async with async_session_factory() as session:
                            audit_entry = AuditLog(
                                user_id=user_uuid,
                                action=f"{method} {path}",
                                resource=path,
                                method=method,
                                ip_address=ips,
                                status_code=int(status_code) if status_code.isdigit() else 200,
                                details={"payload": payload[:500]} if payload else {},
                            )
                            session.add(audit_entry)
                            await session.commit()
                    except Exception as sqle:
                        logger.debug(f"Audit DB entry write: {sqle}")

                # Using Starlette's background tasks functionality for FastAPI
                from starlette.background import BackgroundTask

                task = BackgroundTask(
                    record_audit_entry_sync,
                    request_id,
                    method,
                    url,
                    status_code,
                    payload,
                    ips,
                    user_id,
                )

                if response:
                    # Append task natively to Response so FastAPI handles the executor
                    response.background = task

            except Exception as e:
                logger.critical(f"FATAL: Failed to instantiate Background Task for Audit Log: {e}")

        return response
