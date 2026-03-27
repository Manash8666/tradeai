"""
Financial Escrow Cryptographic Hash Validator (Exit Valuation)

Used strictly securely hashing flat-file CSV dumps of Revenue (Stripe/Bank INR arrays)
proving deterministic integrity of the $1.5M earnout metric to acquirers.
"""

import hashlib
import os
import sys

def generate_earnout_hash(csv_filepath: str) -> str:
    """
    Reads the absolute byte-stream of the Monthly Fiat Revenue Export (CSV) 
    and generates a determinant SHA-256 hash.
    
    This hash is written into the subsequent Asset Purchase Agreement (APA) clause.
    """
    if not os.path.exists(csv_filepath):
        print(f"❌ Error: Revenue report not found at {csv_filepath}")
        return ""

    hasher = hashlib.sha256()
    with open(csv_filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
            
    earnout_hash = hasher.hexdigest()
    
    print("\n" + "="*60)
    print("💰 EARNOUT VERIFICATION HASH GENERATED")
    print("="*60)
    print(f"Target File: {csv_filepath}")
    print(f"SHA-256 Hash: {earnout_hash}")
    print("="*60)
    
    print("\n[LEGAL CLAUSE GENERATOR FOR ASSET PURCHASE AGREEMENT]")
    print(f'''
    "The Sellers assert that the Monthly Platform Revenue metrics utilized to define the 
    ₹1.5 Cr Earnout Tranche match identically to the source data cryptographically 
    verifiable via the SHA-256 hash: [{earnout_hash}]. Any subsequent mutation of the 
    underlying ledger will mathematically alter this hash, triggering immediate Escrow Review."
    ''')
    
    return earnout_hash

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python revenue_hasher.py <path_to_revenue_csv>")
        sys.exit(1)
        
    generate_earnout_hash(sys.argv[1])
