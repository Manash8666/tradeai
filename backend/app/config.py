"""
Application Configuration — Pydantic Settings
All config from environment variables, no hardcoded secrets.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    app_name: str = "TradingPlatform"
    app_env: str = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"  # nosec B104
    app_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # --- Authentication ---
    jwt_secret_key: str  # REQUIRED — no default for security
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # --- PostgreSQL ---
    database_url: str = (
        "postgresql+asyncpg://trading_user:dev_password@localhost:5432/trading_platform"
    )

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- ClickHouse ---
    clickhouse_host: str = "localhost"
    clickhouse_http_port: int = 8123
    clickhouse_db: str = "trading_analytics"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""

    # --- Rate Limiting ---
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # --- CORS ---
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Broker (Static IP — SEBI Compliant) ---
    broker_static_ip: str = ""

    # --- AI / LLM (OpenRouter) ---
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    nemotron_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    liquid_model: str = "liquid/lfm-2.5-1.2b-thinking:free"
    llama_model: str = "meta-llama/llama-3.2-3b-instruct:free"
    llm_request_timeout: int = 60
    llm_max_retries: int = 3

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once from env."""
    return Settings()
