"""
Proprietary Intellectual Property Anchor (Proof Of Existence)

Scans the `ai_agent/` and `core/` directories, generating a Merkle Tree 
representing the exact state of the proprietary code. Submits the root hash
to the OpenTimestamps calendar (Bitcoin L2) establishing an undeniable
cryptographic proof of creation prior to acquisition.
"""

import os
import json
import hashlib
from datetime import datetime, timezone

# We wrap this in a try-except to prevent immediate crash if not installed
try:
    from opentimestamps.core.timestamp import DetachedTimestampFile
    from opentimestamps.core.op import OpSHA256
    import opentimestamps.client as ots_client
except ImportError:
    ots_client = None

TARGET_DIRS = ["ai_agent", "core"]
REGISTRY_PATH = "docs/ip_registry.json"
OTS_OUTPUT_PATH = "docs/ip_anchor.ots"

def hash_file(filepath: str) -> str:
    """Returns SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def sweep_and_hash() -> dict:
    """Sweeps target directories aggregating relative paths and file hashes."""
    file_hashes = {}
    for target in TARGET_DIRS:
        if not os.path.exists(target):
            continue
        for root, _, files in os.walk(target):
            for file in files:
                if file.endswith('.pyc') or '__pycache__' in root:
                    continue
                full_path = os.path.join(root, file)
                # Keep paths relative for portability
                rel_path = os.path.relpath(full_path, start=".")
                file_hashes[rel_path] = hash_file(full_path)
    return file_hashes

def anchor_ip():
    print("=== STARTING IP PROOF OF EXISTENCE ANCHOR ===")
    
    # 1. Sweep proprietary codebases
    file_hashes = sweep_and_hash()
    print(f"Swept {len(file_hashes)} proprietary files across AI/Engine bounds.")
    
    # 2. Build Merkle Root equivalent (Sorting keys to ensure determinism)
    concat_hashes = "".join([file_hashes[k] for k in sorted(file_hashes.keys())])
    merkle_root = hashlib.sha256(concat_hashes.encode('utf-8')).hexdigest()
    
    print(f"Generated Proprietary Merkle Root: {merkle_root}")
    
    # 3. Save Registry
    registry = {
        "project": "AI Trading Platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merkle_root": merkle_root,
        "ots_file": OTS_OUTPUT_PATH,
        "files": file_hashes
    }
    
    os.makedirs("docs", exist_ok=True)
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)
        
    print(f"IP Registry saved locally to {REGISTRY_PATH}")
    
    # 4. Anchor to Bitcoin L2 (OpenTimestamps)
    if ots_client is None:
        print("⚠️ OpenTimestamps module missing. Cannot execute L2 anchor. Run `pip install opentimestamps-client`")
        return
        
    try:
        # We stamp the json registry file itself, which secures the merkle root inside it
        with open(REGISTRY_PATH, "rb") as f:
            file_bytes = f.read()
            
        timestamp = DetachedTimestampFile.from_bytes(OpSHA256(), file_bytes)
        ots_client.stamp(timestamp)
        
        with open(OTS_OUTPUT_PATH, "wb") as f:
            f.write(timestamp.serialize())
            
        print(f"✅ SUCCESS: Cryptographic Proof of Existence generated at {OTS_OUTPUT_PATH}")
        print("Verification Command: `ots verify docs/ip_anchor.ots -f docs/ip_registry.json`")
        
    except Exception as e:
        print(f"❌ FATAL ERROR: OTS Anchoring shattered: {e}")

if __name__ == "__main__":
    anchor_ip()
