"""
Rate Limiting Middleware — Redis-Backed Request Throttling
Configurable per-minute limits with burst support.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.app.config import get_settings

settings = get_settings()

_redis_offline = False
_last_redis_check = 0.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter using Redis.
    Falls back to permissive mode if Redis is unavailable.
    """

    # Paths exempt from rate limiting
    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        global _redis_offline, _last_redis_check
        # Skip exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)  # type: ignore

        now = time.time()
        # Fast path if Redis is known to be offline
        if _redis_offline and (now - _last_redis_check < 60.0):
            return await call_next(request)  # type: ignore

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"

        try:
            # Import here to avoid circular imports and allow graceful degradation
            import redis.asyncio as aioredis

            redis_client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=0.25,
                socket_timeout=0.25,
            )

            key = f"rate_limit:{client_ip}"
            current_time = int(now)
            window_start = current_time - 60  # 1-minute sliding window

            async with redis_client.pipeline(transaction=True) as pipe:
                # Remove old entries outside the window
                await pipe.zremrangebyscore(key, 0, window_start)
                # Count requests in current window
                await pipe.zcard(key)
                # Add current request
                await pipe.zadd(key, {str(current_time * 1000): current_time})
                # Set expiry on the key
                await pipe.expire(key, 120)
                results = await pipe.execute()

            request_count = results[1]
            _redis_offline = False

            if request_count >= settings.rate_limit_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Try again later.",
                        "retry_after": 60,
                    },
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, settings.rate_limit_per_minute - request_count - 1)
            )
            return response  # type: ignore

        except Exception:
            # Redis unavailable — fail open (permissive) and remember for 60s
            _redis_offline = True
            _last_redis_check = now
            return await call_next(request)  # type: ignore
            return await call_next(request)  # type: ignore
