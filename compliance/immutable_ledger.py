"""
Immutable Hash-Chaining Ledger (Compliance & Cryptography)

This module handles the zero-latency SEBI-mandated hashing of all activities 
generating mathematically verifiable proofs. It is fully decoupled from the 
FastAPI networking stack to ensure the execution engine is unblocked.
"""

import hashlib
import logging

from backend.app.database.clickhouse import get_clickhouse_client, get_latest_hash

logger = logging.getLogger(__name__)

def generate_block_hash(previous_hash: str, request_id: str, method: str, url: str, status_code: str, payload: str, ip: str, user_id: str) -> str:
    """
    Cryptographic Hash equivalent to a Bitcoin block generation.
    Binds the absolute payload directly to the timeline of the previous record.
    """
    raw_data = f"{previous_hash}|{request_id}|{method}|{url}|{status_code}|{payload}|{ip}|{user_id}"
    return hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

def record_audit_entry_sync(request_id: str, method: str, url: str, status_code: str, payload: str, ip: str, user_id: str) -> bool:
    """
    Synchronous blocking write strictly appending the block.
    Called asynchronously via background workers locally.
    """
    try:
        prev_hash = get_latest_hash()
        current_hash = generate_block_hash(prev_hash, request_id, method, url, status_code, payload, ip, user_id)
        
        ch_client = get_clickhouse_client()
        cols = ['request_id', 'method', 'url', 'status_code', 'payload', 'ip_addresses', 'user_id', 'previous_hash', 'current_hash']
        data = [[request_id, method, url, status_code, payload[:5000], ip, user_id, prev_hash, current_hash]]
        
        ch_client.insert('audit_logs', data, column_names=cols)
        return True
    except Exception as e:
        logger.critical(f"FATAL: Immutable Ledger generation shattered: {e}")
        return False
