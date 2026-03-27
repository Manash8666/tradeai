# ADR-001: Foundation Architecture & Compliance Decisions

**Status:** Accepted
**Date:** 2026-03-26
**Authors:** AI Agent Team (Lead Architect)
**Reviewers:** Human Lead, Nvidia Nemotron 3 Super AI

---

## Context

We are building an AI-Powered Trading Platform for Indian equity markets, designed as a premium software asset with a target exit valuation of ₹25-50 Lakhs+. The platform must be SEBI-compliant from Day 1, enterprise-grade, and legally defensible.

The original `Trade Platform.pdf` blueprint contains legacy assumptions that conflict with compliance requirements and legal safety. This ADR documents the critical architectural decisions that override the PDF.

---

## Decisions

### 1. Monorepo Architecture

**Decision:** Use a monorepo structure with clearly separated modules.

**Rationale:**
- Single repository simplifies CI/CD, versioning, and code reviews
- Clear boundaries between `core/`, `brokers/`, `data/`, `ai-agent/`, `backend/`, `frontend/`
- Enables parallel development by the AI agent team
- Simplifies license compliance auditing

**Structure:**
```
core/         → NautilusTrader integration
brokers/      → Broker API adapters
data/         → Data pipeline & adapters
ai-agent/     → AI/ML models
backend/      → FastAPI application
frontend/     → React 19 + Vite
infrastructure/ → Docker, deployment
docs/         → ADRs, design system
```

### 2. Static IP Architecture (No IP Rotation)

**Decision:** Use static IP whitelisting exclusively. **NO IP rotation.**

**Rationale:**
- SEBI requires static IP registration for API-based trading
- IP rotation violates broker Terms of Service (Angel One, Zerodha)
- Any IP rotation code would make the asset unsellable
- Static IP is a hard requirement for production broker connectivity

**Override:** PDF Section 2.2 suggests IP rotation. This is **REJECTED**.

### 3. Licensed Data Providers (Adapter Pattern)

**Decision:** Build abstract Data Adapter interfaces. Free sources are dev-only.

**Rationale:**
- Production trading requires licensed, reliable data feeds
- TrueData and GlobalDataFeeds are the target providers
- Free scraping (nsefin, etc.) is unreliable and may violate ToS
- Adapter pattern allows swapping providers without code changes

**Override:** PDF Sections 2.3 & 7 suggest free scraping for production. This is **DEV ONLY**.

### 4. NautilusTrader as Attributed Dependency

**Decision:** Use NautilusTrader as a `pip install` dependency with full attribution.

**Rationale:**
- NautilusTrader is Apache 2.0 licensed — attribution is required
- Hiding the dependency creates legal liability
- Our value-add is in Adapters, AI models, UI/UX, and Compliance layers
- Clean dependency management simplifies upgrades

**Override:** PDF Section 2.1 implies presenting NautilusTrader as proprietary. This is **REJECTED**.

### 5. Compliance-Ready from Day 1

**Decision:** Build audit logging, Algo ID fields, and compliance endpoints from the foundation.

**Rationale:**
- Retrofitting compliance is 5-10x more expensive than building it in
- SEBI requires complete audit trails for algorithmic trading
- Algo ID tracking is mandatory for regulatory reporting
- Immutable audit logs prevent tampering

**Implementation:**
- `AuditLog` model with immutable entries (no UPDATE/DELETE)
- Every API request logged with user, IP, action, timestamp
- `algo_id` field on audit logs for SEBI algo identification
- `/compliance/status` endpoint for compliance monitoring

### 6. Security Architecture

**Decision:** JWT via HTTPOnly cookies, bcrypt password hashing, Redis rate limiting.

**Rationale:**
- HTTPOnly cookies prevent XSS token theft (vs localStorage)
- bcrypt with 12 rounds provides strong password hashing
- Redis sliding window rate limiting prevents abuse
- Session tracking enables token revocation

---

## Consequences

### Positive
- Platform is legally defensible and SEBI-compliant from Day 1
- Clean architecture enables parallel development
- Adapter pattern provides flexibility for data/broker providers
- Security best practices mitigate OWASP Top 10

### Negative
- Static IP limits deployment flexibility (must register IP with brokers)
- Licensed data feeds have ongoing costs
- Compliance overhead adds development time upfront

### Risks
- Free data sources may be insufficient for development testing
- NautilusTrader API changes may require adapter updates

---

## References

- SEBI Circular on Algorithmic Trading (SEBI/HO/MRD/DP/CIR/P/2021/127)
- NautilusTrader License: Apache 2.0
- OWASP Top 10 (2021)
- Trade Platform.pdf (original blueprint — superseded by this ADR)
