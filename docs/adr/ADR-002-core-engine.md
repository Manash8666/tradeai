# ADR-002: Core Engine & Broker Architecture

**Status:** Accepted
**Date:** 2026-03-26
**Authors:** AI Agent Team (Lead Architect)
**Reviewers:** Human Lead

---

## Context

For Phase 1 of the AI-Powered Trading Platform, we needed to define the architecture for trade execution, market data digestion, and strict compliance enforcement (static IP usage and Algo ID tracking). The platform must also support risk-free algorithm testing (Paper Trading) mimicking the live environment perfectly.

---

## Decisions

### 1. NautilusTrader Integration Model
**Decision:** Wrap `NautilusTrader` inside an asynchronous FastAPI facade (`core/engine.py`).
**Rationale:** Nautilus is extremely fast and robust for execution but is synchronous in many of its core loops depending on Cython structures. Wrapping the `TradingNode` in an `async` lifecycle ensures our FastAPI instance can control it without blocking API requests. 
**Compliance:** The engine node is strictly named and runs behind our auth layer.

### 2. Message Bus Architecture
**Decision:** Create a lightweight `MessageBus` (`core/message_bus.py`) acting as a Pub/Sub bridge between the trading thread and the async WebSockets layer.
**Rationale:** Real-time feedback is required for the React Dashboard. WebSockets are ideal for push events (order filled, tick updates). The Message Bus decouples the trading logic from the networking logic.

### 3. Broker Adapters & Angel One
**Decision:** Implement an `AngelOneAdapter` using `Brokers/base.py` interface.
**Rationale:** Angel One's SmartAPI will be the first production broker.
**Compliance Override:** As per Phase 0 agreements, **NO IP ROTATION** is implemented. The adapter rigorously checks for `BROKER_STATIC_IP`.
**Algo ID:** The `translator.py` protocol maps standard orders to SmartAPI syntax and legally injects the SEBI `algo_id` as an `ordertag`.

### 4. Data Adapters & Mocking
**Decision:** Standardize quotes into a uniform `MarketQuote` dataclass regardless of whether the source is `TrueData` or the `DevMockFeed`.
**Rationale:** Simplifies strategy development. Strategies only understand `MarketQuote`. The `PaperBroker` and `DevDataAdapter` provide a closed-loop system for algorithmic safety checks before deploying to `AngelOne`.

---

## Consequences

### Positive
- Strict separation of concerns (Broker Logic vs Data Logic vs Engine Execution).
- Paper trading pipeline allows 100% safe UI/UX testing.
- Platform is insulated from upstream Broker API changes since they flow through our `translator.py`.

### Negative
- Mock data generation lacks realistic depth-of-market and latency curves compared to live TrueData streams.
- Wrapping Nautilus in AsyncIO requires careful lock management (`asyncio.Lock()` in `EngineWrapper`) to prevent concurrent modification of the engine state via REST API endpoints.
