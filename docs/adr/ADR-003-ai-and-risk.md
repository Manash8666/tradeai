# ADR-003: AI Pipeline & Pre-Trade Risk Architecture

**Status:** Accepted
**Date:** 2026-03-26
**Authors:** AI Agent Team (Lead Architect)
**Reviewers:** Human Lead

---

## Context

For **Phase 2** of the platform, we needed to establish the "Brain" of the operation—the AI models that generate buy/sell signals off streaming market data. Concurrently, since automated intelligence inherently carries systemic risk, we required an impenetrable Pre-Trade Risk Management engine that evaluates every single order BEFORE it hits the `BrokerAdapter`. Finally, the strategies required validation against historical market data via a high-performance backtesting harness.

---

## Decisions

### 1. ML Stack Separation
**Decision:** We deferred PyTorch/TensorFlow to Phase 3. Phase 2 strictly uses `scikit-learn`, `numpy`, and `pandas`.
**Rationale:** It allows us to prove the architecture end-to-end with a deterministic statistical baseline (Z-Score Mean Reversion) without introducing massive GPU dependencies and Docker bloating prematurely. The `ai_agent/models/base.py` enforces a generic `predict(features)` signature so swapping to Deep Learning later is perfectly seamless.

### 2. Risk Intercept Pattern
**Decision:** The `RiskManager` instance explicitly intercepts the `.place_order()` method inside **all** Broker Adapters (`AngelOneAdapter`, `PaperBroker`, etc.).
**Rationale:** Hard-stopping orders closest to the exchange layer provides maximum safety. The `validate_pre_trade` evaluates three absolute rules:
1. **Fat Finger / Rogue Algorithmic Spikes:** Rejects quantities > `max_single_order_qty` (e.g., 1000).
2. **Max Daily Drawdown:** Calculates `(Start_Equity - Net_Liquidity) / Start_Equity`. Shuts off trading globally if breached (e.g., > 5%).
3. **Symbol Exposure Limits (Leverage):** Rejects orders that push allocation in a single stock above `20%` of portfolio Net Liquidity.

### 3. Asynchronous Model Inference execution
**Decision:** `AITradingStrategy` runs as a high-performance Nautilus `Strategy` block. Every Nth quote tick, it slices its `tick_buffer` into `features` and calls `inference_engine.run_inference()` synchronously, but utilizes `asyncio.get_running_loop().create_task` to publish signals to the `message_bus` for the WebSockets.
**Rationale:** This ensures the execution speed of the Nautilus loop isn't bottlenecked by waiting on WebSockets or HTTP streams hitting the React UI.

### 4. Backtesting Gateway
**Decision:** Wrap the Rust-native `nautilus_trader.backtest.engine.BacktestEngine` and expose it via the backend as a `POST /trading/backtest/run` REST API.
**Rationale:** Enables the React Dashboard to act as a central hub not just for live operations, but for researching and simulating strategies against local ClickHouse datasets dynamically.

---

## Consequences

### Positive
- Strict isolation of the "Thinking Engine" (AI Pipeline) from the "Execution Engine" (Nautilus).
- The Pre-Trade hooks guarantee that even if an AI model hallucinates a 50,000 QTY order, the system will raise `RiskViolationException` natively and protect the live account.

### Negative
- ML algorithms like Random Forests and strict Statistical Z-Scores might require significant history pre-loaded on Startup to generate the first few signals. The Data Pipeline must account for this warmup period.
