# Design System v0.1

**AI Trading Platform — Visual Identity & Component Guidelines**
**Version:** 0.1.0 | **Date:** 2026-03-26

---

## Design Philosophy

Premium, data-dense trading interface optimized for extended use sessions. Dark theme reduces eye strain during market hours. Glassmorphism creates visual depth and hierarchy.

**Principles:**
1. **Clarity** — Data readability is paramount
2. **Depth** — Layered glass effects create information hierarchy
3. **Motion** — Subtle animations confirm interactions, not distract
4. **Density** — Maximum information per viewport for professional traders

---

## Color Palette

### Primary — Deep Ocean
| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary-300` | `#5bb5ee` | Accent text, links |
| `--color-primary-500` | `#0d8bd0` | Primary actions, CTA |
| `--color-primary-700` | `#074d74` | Active states |

### Semantic
| Token | Hex | Usage |
|-------|-----|-------|
| `--color-profit` | `#00e676` | Positive P&L, green candles |
| `--color-loss` | `#ff1744` | Negative P&L, red candles |
| `--color-success-400` | `#34d399` | System healthy, confirmations |
| `--color-warning-400` | `#fbbf24` | Warnings, pending states |
| `--color-danger-400` | `#fb7185` | Errors, critical alerts |

### Backgrounds
| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg-primary` | `#0b1120` | Page background |
| `--color-bg-secondary` | `#111827` | Section background |
| `--color-bg-card` | `rgba(17,24,39,0.7)` | Card surfaces |

---

## Typography

| Element | Font | Weight | Size |
|---------|------|--------|------|
| Headings | Inter | 700-800 | 1.25-2rem |
| Body | Inter | 400-500 | 0.875-1rem |
| Labels | Inter | 600 | 0.75rem, uppercase, 0.1em tracking |
| Code/Data | JetBrains Mono | 400-500 | 0.75-0.875rem |

---

## Glassmorphism Specification

```css
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
```

**Hover:** Border brightens to `rgba(255,255,255,0.15)`, card lifts 2px.

---

## Motion Guidelines (Framer Motion)

| Type | Duration | Easing | Example |
|------|----------|--------|---------|
| Enter | 400-600ms | `[0.4, 0, 0.2, 1]` | Card appear, page transition |
| Micro | 150-250ms | `[0.4, 0, 0.2, 1]` | Button hover, toggle |
| Data update | 200ms | `ease-out` | Number change, chart tick |
| Stagger | +80-100ms | Sequential | List items, grid cards |

**Rules:**
- No animation >600ms
- Stagger children with 80-100ms delay
- Reduce motion for `prefers-reduced-motion`
- 60fps target — GPU-accelerated transforms only

---

## Component Inventory (v0.1)

| Component | Status | Description |
|-----------|--------|-------------|
| `Header` | ✅ | Sticky, glassmorphism backdrop, gradient branding |
| `StatusCard` | ✅ | Metric display with status indicator |
| `ComplianceBadge` | ✅ | SEBI compliance checklist |
| `Dashboard` | ✅ | Health monitoring layout |
| `useWebSocket` | ✅ | Real-time data hook with auto-reconnect |
