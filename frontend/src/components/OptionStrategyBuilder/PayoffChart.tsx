import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import type { StrategyAnalysisResult } from './types';

interface PayoffChartProps {
  analysis: StrategyAnalysisResult;
  targetDays: number;
  onTargetDaysChange: (days: number) => void;
  ivShift: number;
  onIvShiftChange: (iv: number) => void;
}

export function PayoffChart({
  analysis,
  targetDays,
  onTargetDaysChange,
  ivShift,
  onIvShiftChange,
}: PayoffChartProps) {
  const { payoff_curve, spot, breakevens, max_profit_inr, max_loss_inr, risk_reward, pop_pct, net_credit_debit_inr, margin_required_inr, net_greeks } = analysis;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      {/* ── TOP METRICS CARDS ───────────────────────────────────────────── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
          gap: 'var(--space-2)',
          padding: 'var(--space-2) var(--space-3)',
          background: 'var(--color-bg-secondary)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div>
          <span style={{ fontSize: '0.58rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Max Profit</span>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--color-success)', fontFamily: 'var(--font-mono)' }}>
            {max_profit_inr === null ? 'Unlimited' : `₹${max_profit_inr.toLocaleString('en-IN')}`}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.58rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Max Loss</span>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--color-error)', fontFamily: 'var(--font-mono)' }}>
            {max_loss_inr === null ? 'Unlimited' : `₹${max_loss_inr.toLocaleString('en-IN')}`}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.58rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Risk : Reward</span>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
            {risk_reward}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.58rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Prob of Profit (POP)</span>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: pop_pct >= 60 ? 'var(--color-success)' : (pop_pct <= 40 ? 'var(--color-error)' : 'var(--color-warning)'), fontFamily: 'var(--font-mono)' }}>
            {pop_pct}%
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.58rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Net Premium</span>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: net_credit_debit_inr >= 0 ? 'var(--color-success)' : 'var(--color-error)', fontFamily: 'var(--font-mono)' }}>
            {net_credit_debit_inr >= 0 ? `+₹${net_credit_debit_inr.toLocaleString('en-IN')}` : `-₹${Math.abs(net_credit_debit_inr).toLocaleString('en-IN')}`}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.58rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Est. Margin</span>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--color-primary)', fontFamily: 'var(--font-mono)' }}>
            ₹{margin_required_inr.toLocaleString('en-IN')}
          </div>
        </div>
      </div>

      {/* ── BREAKEVENS & GREEKS RIBBON ──────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.65rem', color: 'var(--color-text-muted)', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
        <div>
          <strong>Breakeven(s):</strong>{' '}
          {breakevens.length > 0 ? (
            breakevens.map((b) => (
              <span key={b} className="badge badge-sm" style={{ marginRight: 4, fontFamily: 'var(--font-mono)' }}>
                ₹{b.toFixed(1)}
              </span>
            ))
          ) : (
            <span>None</span>
          )}
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-3)', fontFamily: 'var(--font-mono)' }}>
          <span>Δ: <strong>{net_greeks.delta.toFixed(2)}</strong></span>
          <span>Γ: <strong>{net_greeks.gamma.toFixed(4)}</strong></span>
          <span>θ: <strong>₹{net_greeks.theta.toFixed(0)}/d</strong></span>
          <span>ν: <strong>{net_greeks.vega.toFixed(1)}</strong></span>
        </div>
      </div>

      {/* ── INTERACTIVE PAYOFF CHART ────────────────────────────────────── */}
      <div
        style={{
          width: '100%',
          height: 280,
          background: 'var(--color-bg-primary)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          padding: '8px',
          position: 'relative',
        }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={payoff_curve} margin={{ top: 10, right: 15, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="lossGrad" x1="0" y1="1" x2="0" y2="0">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <XAxis
              dataKey="price"
              domain={['auto', 'auto']}
              tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
              tickFormatter={(v) => `₹${v}`}
            />
            <YAxis
              tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
              tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
            />

            <Tooltip
              content={({ active, payload: tPayload }) => {
                if (active && tPayload && tPayload.length) {
                  const dataPoint = tPayload[0].payload;
                  return (
                    <div
                      style={{
                        background: 'rgba(15, 23, 42, 0.95)',
                        border: '1px solid var(--color-border)',
                        padding: '6px 10px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.68rem',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      <div style={{ color: '#fff', fontWeight: 700 }}>Underlying: ₹{dataPoint.price}</div>
                      <div style={{ color: dataPoint.pnl_expiry >= 0 ? '#22c55e' : '#ef4444' }}>
                        Expiry P&L: ₹{dataPoint.pnl_expiry.toLocaleString('en-IN')}
                      </div>
                      <div style={{ color: dataPoint.pnl_today >= 0 ? '#38bdf8' : '#f87171' }}>
                        T+{targetDays} P&L: ₹{dataPoint.pnl_today.toLocaleString('en-IN')}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />

            {/* Zero line */}
            <ReferenceLine y={0} stroke="rgba(255,255,255,0.25)" strokeWidth={1} />

            {/* Current Spot Reference line */}
            <ReferenceLine
              x={spot}
              stroke="var(--color-primary)"
              strokeDasharray="3 3"
              label={{ value: `Spot: ₹${spot.toFixed(0)}`, fill: 'var(--color-primary)', fontSize: 10, position: 'top' }}
            />

            {/* Breakeven lines */}
            {breakevens.map((b) => (
              <ReferenceLine key={b} x={b} stroke="#eab308" strokeDasharray="2 2" />
            ))}

            <Area
              type="monotone"
              dataKey="pnl_expiry"
              stroke="#22c55e"
              strokeWidth={2}
              fill="url(#profitGrad)"
              name="Expiry P&L"
            />
            <Area
              type="monotone"
              dataKey="pnl_today"
              stroke="#38bdf8"
              strokeWidth={1.5}
              strokeDasharray="4 2"
              fill="none"
              name="T+0 P&L"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* ── TARGET DATE & IV SLIDERS ─────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem' }}>
            <span style={{ color: 'var(--color-text-muted)' }}>Target Date ({targetDays} DTE)</span>
            <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>{targetDays} Days</span>
          </div>
          <input
            type="range"
            min={0}
            max={20}
            step={0.5}
            value={targetDays}
            onChange={(e) => onTargetDaysChange(parseFloat(e.target.value))}
            className="w-full"
            style={{ accentColor: 'var(--color-primary)' }}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem' }}>
            <span style={{ color: 'var(--color-text-muted)' }}>IV Shift ({ivShift > 0 ? `+${ivShift}%` : `${ivShift}%`})</span>
            <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>{ivShift > 0 ? `+${ivShift}%` : `${ivShift}%`}</span>
          </div>
          <input
            type="range"
            min={-10}
            max={10}
            step={0.5}
            value={ivShift}
            onChange={(e) => onIvShiftChange(parseFloat(e.target.value))}
            className="w-full"
            style={{ accentColor: 'var(--color-primary)' }}
          />
        </div>
      </div>
    </div>
  );
}
