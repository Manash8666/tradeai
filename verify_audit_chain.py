"""
Immutable Ledger Mathematical Cryptography Validator

A pure validation loop executed natively sweeping the identical `audit_logs` 
ClickHouse MergeTree array proving the absolute integrity of every single Hash Chain element.
Crucial for passing Third-Party Security Due-Diligence without any trust requirements.
"""

import logging
import hashlib
from backend.app.database.clickhouse import get_clickhouse_client

logger = logging.getLogger(__name__)

def verify_audit_ledger() -> bool:
    c = get_clickhouse_client()
    try:
        # Fetch the entire ledger deterministically ordered
        res = c.query("SELECT request_id, method, url, status_code, payload, ip_addresses, user_id, previous_hash, current_hash FROM audit_logs ORDER BY timestamp ASC")
        rows = res.result_rows
        
        if not rows:
            print("Ledger is entirely empty. Simulation Pass.")
            return True

        print(f"Sweeping {len(rows)} blocks across the ClickHouse MergeTree...")
        
        expected_prev_hash = "GENESIS_BLOCK_00000000"
        
        for i, row in enumerate(rows):
            req_id, method, url, status, payload, ip, usr, prev_h, current_h = row
            
            # 1. Does the block link accurately to the history?
            if prev_h != expected_prev_hash:
                print(f"❌ TAMPER ERROR at Block #{i} ({req_id}): 'previous_hash' link broken!")
                return False
                
            # 2. Is the current payload un-altered mathematically?
            raw_data = f"{prev_h}|{req_id}|{method}|{url}|{status}|{payload}|{ip}|{usr}"
            calculated_hash = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()
            
            if calculated_hash != current_h:
                print(f"❌ TAMPER ERROR at Block #{i} ({req_id}): Payload mutation detected mathematically. Expected '{current_h}', Got '{calculated_hash}'!")
                return False
                
            # Success: Move to verify next block in loop
            expected_prev_hash = current_h
            
        print("✅ LEDGER VALIDATED: Cryptographic integrity absolute.")
        return True
        
    except Exception as e:
        print(f"Ledger Verification Pipeline Execution Halt: {e}")
        return False

if __name__ == "__main__":
    verify_audit_ledger()
