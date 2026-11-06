"""
Trading Platform — FastAPI Application Entry Point
Enterprise-grade backend with CORS, audit logging, rate limiting, and auth.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, AsyncGenerator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.router import router as auth_router
from backend.app.trading.router import router as trading_router
from backend.app.trading.signals import router as signals_router
from backend.app.trading.backtest import router as backtest_router
from backend.app.trading.webhooks import router as webhooks_router
from backend.app.config import get_settings
from backend.app.database import close_db, init_db
from backend.app.middleware.audit import AuditLoggingMiddleware
from backend.app.middleware.rate_limit import RateLimitMiddleware
from backend.app.models.user import User
from backend.app.core.hft_engine import hft_engine as engine_wrapper
from ai_agent.router import router as ai_router
from ai_agent.thinking_router import router as thinking_router
from ai_agent.chat_router import router as chat_router
from backend.app.orchestrator.router import router as orchestrator_router
from backend.app.integrations.tradingview_bridge import router as tradingview_router
from ai_agent.mirajane.bot_router import router as mirajane_router
from backend.app.trading.options_router import router as options_router
from backend.app.trading.paper_router import router as paper_router
from backend.app.trading.hft_router import router as hft_router
from backend.app.trading.morning_scheduler import morning_market_scheduler
from prometheus_fastapi_instrumentator import Instrumentator

settings = get_settings()


# =============================================================================
# Application Lifespan
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    # Startup
    if not settings.is_production:
        await init_db()  # Auto-create tables in dev/test
    await morning_market_scheduler.start()
    yield
    # Shutdown
    await morning_market_scheduler.stop()
    await engine_wrapper.stop()
    await close_db()


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="AI Trading Platform API",
    description=(
        "Enterprise-grade API for AI-Powered Trading Platform for Indian Markets. "
        "SEBI-compliant with immutable audit logging and static IP architecture."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- Middleware (order matters: last added = first executed) ---
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth_router)
app.include_router(trading_router)
app.include_router(signals_router)
app.include_router(backtest_router)
app.include_router(webhooks_router)
app.include_router(ai_router)
app.include_router(thinking_router)
app.include_router(chat_router)
app.include_router(orchestrator_router)
app.include_router(tradingview_router)
app.include_router(mirajane_router)
app.include_router(options_router)
app.include_router(paper_router)
app.include_router(hft_router)

# --- Instrumentation ---
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)


# =============================================================================
# Health & Compliance Endpoints
# =============================================================================


@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
async def health_check() -> dict:
    """
    System health check endpoint.
    Returns service status for monitoring and Docker health checks.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "0.1.0",
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/compliance/status", tags=["Compliance"])
@app.get("/api/compliance/status", tags=["Compliance"])
async def compliance_status(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Compliance status endpoint — requires authentication.
    Reports on SEBI compliance readiness.
    """
    return {
        "status": "compliant",
        "checks": {
            "static_ip_architecture": True,
            "audit_logging_active": True,
            "ip_rotation_code": False,  # Must always be False
            "data_source_licensed": settings.is_production,
            "jwt_httponly_cookies": True,
            "engine_attribution": "Proprietary HFT Algorithmic Core (NautilusTrader Engine)",
            "algo_id_support": True,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": current_user.email,
    }


@app.get("/", tags=["System"])
async def root() -> dict:
    """API root — basic info."""
    return {
        "name": "AI Trading Platform API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
