# ADR-001: Foundation Architecture & Blockchain Constraints

**Status:** Accepted
**Date:** 2026-03-26
**Authors:** AI Agent Team (Lead Architect)
**Reviewers:** Human Lead

---

## Context
The AI-Powered Trading Platform requires a highly robust foundational architecture supporting extreme latency tolerances while satisfying the severe regulatory reporting required by Indian Equity Markets (SEBI). Furthermore, preparing the software asset for acquisition entails maximizing system trust properties without inflating regulatory exposure.

## Decision

### 1. Monorepo Structure & Containerization
We will adopt a multi-tier containerized Monorepo executing across stateless isolated Docker containers.
- `backend/` serves the control plane (FastAPI).
- `core/` wraps the Rust-based NautilusTrader execution engine.
- `ai_agent/` maintains Python-based ML inferencing models.

### 2. Static IP Enforcement
SEBI unequivocally forbids algorithmic execution through proxy rotations, VPN pooling, or masked egress routers. 
All connectivity into Angel One/Zerodha MUST route originating from a statically assigned IP Address matching the Broker's whitelist strictly registered to the exchange.

### 3. Cryptographic Blockchain Isolation (Phase 4.5 Addition)
To maximize the M&A valuation multiples, we require mechanisms proving the systemic integrity of the platform's logs and proprietary IP without trusting the host server.

**Limitation:** We CANNOT deploy cryptocurrency token assets, wallet signatures, or token-based settlement layers under the authority of the RBI without facing severe tax and operational blockades.

**Architecture:**
- Execution telemetry is cryptographically "Hash-Chained" inside ClickHouse via SHA-256 matching.
- Valuation IP Merkle Roots are aggregated via `anchor_ip_hash.py` and stamped into Bitcoin L2 using `opentimestamps-client` asynchronously.
- Absolutely zero actual token transfers happen locally. The system operates strictly in INR fiat.

## Consequences
- **Positive:** Buyers can execute zero-trust audits verifying log validity mathematically. Valuation metrics are sealed securely.
- **Negative:** Increased complexity in logging pipelines migrating away from native PostgreSQL. We mitigate this through dedicated Clickhouse deployments handling massive I/O sequences safely.
