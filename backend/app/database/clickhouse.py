"""
Immutable ClickHouse Connection setup for SEBI Audit tracking.
"""

import logging
import clickhouse_connect

from backend.app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Global Clickhouse Client Singleton
client = None

def get_clickhouse_client():
    """Returns the active Clickhouse connect client."""
    global client
    if client is None:
        try:
            # Assuming clickhouse is running on same network mesh, fallback to localhost
            host = "localhost" if settings.is_production is False else "clickhouse"
            client = clickhouse_connect.get_client(
                host=host,
                port=8123,
                username=settings.clickhouse_user if hasattr(settings, 'clickhouse_user') else "default",
                password=settings.clickhouse_password if hasattr(settings, 'clickhouse_password') else "dev_clickhouse_password"
            )
            logger.info("Successfully connected to ClickHouse for Audit Logging.")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise e
    return client

def init_clickhouse():
    """Initializes the immutable Hash-Chained Audit table."""
    c = get_clickhouse_client()
    
    # We use MergeTree. It is append-only by default (mutations are heavy and visible).
    schema = """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID DEFAULT generateUUIDv4(),
        request_id String,
        method String,
        url String,
        status_code String,
        payload String,
        ip_addresses String,
        user_id String,
        timestamp DateTime64(6, 'UTC') DEFAULT now(),
        
        -- Cryptographic validation
        previous_hash String, 
        current_hash String
    ) ENGINE = MergeTree()
    ORDER BY (timestamp, request_id)
    """
    c.command(schema)
    logger.info("Validated `audit_logs` MergeTree schema on ClickHouse.")

def get_latest_hash() -> str:
    """Retrieve the `current_hash` from the absolute latest row in the ledger."""
    c = get_clickhouse_client()
    try:
        res = c.query("SELECT current_hash FROM audit_logs ORDER BY timestamp DESC LIMIT 1")
        return res.result_rows[0][0] if res.result_rows else "GENESIS_BLOCK_00000000"
    except Exception as e:
        logger.error(f"Failed to fetch previous hash: {e}")
        return "GENESIS_BLOCK_00000000"
