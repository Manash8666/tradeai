# Blockchain Compliance & IP Validation (Zero-Trust Standard)

## Overview
This document outlines the strict integration policies governing the AI Trading Platform's usage of cryptographic hashing. 

Because the platform operates mathematically mapped to the **National Stock Exchange (NSE)** and **Bombay Stock Exchange (BSE)**, it falls permanently under the strict regulatory umbrellas of **SEBI** and the **Reserve Bank of India (RBI)**.

## The Zero-Crypto Policy
The integration of blockchain mathematics in this application is **strictly for data verification, provenance, and tamper-evidence**.

✅ **PERMITTED USE CASES:**
1. **Audit Hash-Chaining:** Cryptographically linking the `previous_hash` of a system event to the `current_hash` preventing database mutations.
2. **IP Proof of Existence:** Generating Merkle roots of the proprietary codebase and anchoring them to the Bitcoin L2 chain via OpenTimestamps.
3. **Escrow Earnouts:** Generating offline SHA-256 hashes of Strike/INR bank exports manually for insertion into Legal M&A documents.

❌ **PROHIBITED USE CASES (Firewall Ruptures):**
1. **No Token Settlement:** SEBI mandates T+1 fiat settlement through the NSCCL. The core engine is forbidden from routing executions derived from or settling into ERC-20/SPL configurations.
2. **No External Smart Contracts:** The system does NOT hold private keys that sign transactions moving capital.
3. **Zero-Latency Constraints:** Operations generating Bitcoin anchors (OpenTimestamps) MUST occur outside the primary `async` trading event loop using isolated BackgroundTasks. Cryptography cannot induce >10ms delays on live market data ingress.

## Conclusion
Buyers executing Due Diligence mapping against the platform's valuation can mathematically verify data integrity via `verify_audit_chain.py` without absorbing any regulatory crypto-asset execution liabilities into their portfolio.
