# Phase 5.5 Integration Plan (Valuation Enhancer)

## 1. State Management Migration (Zustand + TanStack Query)
- **Current:** Localized `useState` cascading props causing mid-tier re-renders on the main `Dashboard.tsx` grid.
- **Incoming Architecture:**
  1. `store/portfolioStore.ts`: Zustand store isolating equity, P&L, and position limits natively. Let React subscribe selectively.
  2. `hooks/useMarketData.ts`: Wraps `TanStack Query` bridging the FastAPI telemetry polling (`/api/health` and `/api/compliance/status`), automatically handling background retries gracefully.
- **Estimated Effort:** 1 Day.

## 2. Options Heatmap Acceleration (WebWorkers)
- **Current:** Raw HTML5 `<canvas>` rendering 1,000 cells directly on the main UI thread via `requestAnimationFrame`. Fast, but blocks React interactivity during heavy localized volume events.
- **Incoming Architecture:**
  - Extract the math/graphics pipeline into `heatmap.worker.ts`.
  - The React Component (`OptionsHeatmap.tsx`) simply passes an `OffscreenCanvas` to the worker allowing it to compute 60FPS fluid maps entirely decoupled from DOM operations.
- **Estimated Effort:** 1 Day.

## 3. Compliance Visibility API (Interactive Trust Ledger)
- **Current:** The `ComplianceBadge` operates on static configuration metrics visualizing "Verified" states locally.
- **Incoming Architecture:**
  - Integrate a click-handler directly pulling the authentic Hash-Chained state originating from `immutable_ledger.py`.
  - Modal exposes the raw `SHA-256` Bitcoin L2 OpenTimestamps root proving temporal existence.
- **Estimated Effort:** 0.5 Days.

## 4. Documentation & Storybook
- **Incoming Architecture:**
  - Execute `npx storybook@latest init`.
  - Isolate the `ComplianceBadge`, `OptionsHeatmap`, and Glassmorphism blocks allowing external DD tech teams to audit components perfectly without spinning up the backend Docker mesh.
- **Estimated Effort:** 1-2 Days.
