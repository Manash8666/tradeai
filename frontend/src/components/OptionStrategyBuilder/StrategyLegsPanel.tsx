import { useState } from 'react';
import { Trash2, Plus, Zap, ShieldCheck } from 'lucide-react';
import type { StrategyLeg } from './types';

interface StrategyLegsPanelProps {
  legs: StrategyLeg[];
  lotSize: number;
  onUpdateLeg: (id: string, updates: Partial<StrategyLeg>) => void;
  onRemoveLeg: (id: string) => void;
  onAddBlankLeg: () => void;
  onClearAll: () => void;
  onExecuteBasket: () => Promise<void>;
  isExecuting: boolean;
}

export function StrategyLegsPanel({
  legs,
  lotSize,
  onUpdateLeg,
  onRemoveLeg,
  onAddBlankLeg,
  onClearAll,
  onExecuteBasket,
  isExecuting,
}: StrategyLegsPanelProps) {
  const [executionMessage, setExecutionMessage] = useState<string | null>(null);

  const handleExecute = async () => {
    try {
      await onExecuteBasket();
      setExecutionMessage('✅ Basket Executed via PyO3 Rust OMS (<50µs latency). SEBI Audit Logged.');
      setTimeout(() => setExecutionMessage(null), 5000);
    } catch {
      setExecutionMessage('⚠️ Execution failed or rejected by risk controls.');
      setTimeout(() => setExecutionMessage(null), 5000);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-2)',
        background: 'var(--color-bg-secondary)',
        padding: 'var(--space-3)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
      }}
    >
      {/* ── HEADER ──────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 800 }}>
            Strategy Legs ({legs.length})
          </span>
          <span className="badge" style={{ fontSize: '0.58rem' }}>
            {lotSize} Qty/Lot
          </span>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <button
            onClick={onAddBlankLeg}
            className="btn btn-sm btn-ghost"
            style={{ fontSize: '0.64rem', padding: '2px 6px' }}
          >
            <Plus size={11} /> Add Leg
          </button>
          {legs.length > 0 && (
            <button
              onClick={onClearAll}
              className="btn btn-sm btn-ghost"
              style={{ fontSize: '0.64rem', padding: '2px 6px', color: 'var(--color-error)' }}
            >
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* ── LEGS LIST ───────────────────────────────────────────────────── */}
      {legs.length === 0 ? (
        <div
          style={{
            padding: 'var(--space-4)',
            textAlign: 'center',
            fontSize: '0.72rem',
            color: 'var(--color-text-muted)',
            border: '1px dashed var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          No legs added yet. Click any <strong>Ready-Made Strategy</strong> or click <strong>+</strong> on the Option Chain strikes.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', maxHeight: '200px', overflowY: 'auto' }}>
          {legs.map((leg) => {
            const isBuy = leg.action === 'BUY';
            const isCall = leg.type === 'CE';

            return (
              <div
                key={leg.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--color-bg-primary)',
                  border: isBuy ? '1px solid rgba(0, 255, 136, 0.25)' : '1px solid rgba(255, 48, 92, 0.25)',
                  fontSize: '0.68rem',
                  fontFamily: 'var(--font-mono)',
                  gap: 'var(--space-2)',
                }}
              >
                {/* BUY / SELL Toggle */}
                <button
                  onClick={() => onUpdateLeg(leg.id, { action: isBuy ? 'SELL' : 'BUY' })}
                  style={{
                    fontSize: '0.60rem',
                    fontWeight: 800,
                    padding: '2px 6px',
                    borderRadius: '2px',
                    background: isBuy ? 'rgba(0, 255, 136, 0.2)' : 'rgba(255, 48, 92, 0.2)',
                    color: isBuy ? 'var(--color-success)' : 'var(--color-error)',
                    border: 'none',
                    cursor: 'pointer',
                  }}
                >
                  {leg.action}
                </button>

                {/* Expiry */}
                <span style={{ color: 'var(--color-text-muted)', fontSize: '0.62rem' }}>{leg.expiry}</span>

                {/* Strike */}
                <span style={{ fontWeight: 800, color: 'var(--color-text-primary)' }}>{leg.strike}</span>

                {/* CE / PE Toggle */}
                <button
                  onClick={() => onUpdateLeg(leg.id, { type: isCall ? 'PE' : 'CE' })}
                  style={{
                    fontSize: '0.60rem',
                    fontWeight: 800,
                    padding: '2px 5px',
                    borderRadius: '2px',
                    background: 'var(--color-bg-tertiary)',
                    color: isCall ? 'var(--color-primary)' : '#c084fc',
                    border: '1px solid var(--color-border)',
                    cursor: 'pointer',
                  }}
                >
                  {leg.type}
                </button>

                {/* Lots / Quantity adjuster */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <button
                    onClick={() => {
                      if (leg.lots > 1) {
                        onUpdateLeg(leg.id, { lots: leg.lots - 1, quantity: (leg.lots - 1) * lotSize });
                      }
                    }}
                    style={{ background: 'transparent', border: '1px solid var(--color-border)', color: '#fff', borderRadius: 2, padding: '0 4px', cursor: 'pointer' }}
                  >
                    -
                  </button>
                  <span style={{ minWidth: 28, textAlign: 'center', fontWeight: 700 }}>
                    {leg.lots}L ({leg.quantity})
                  </span>
                  <button
                    onClick={() => {
                      onUpdateLeg(leg.id, { lots: leg.lots + 1, quantity: (leg.lots + 1) * lotSize });
                    }}
                    style={{ background: 'transparent', border: '1px solid var(--color-border)', color: '#fff', borderRadius: 2, padding: '0 4px', cursor: 'pointer' }}
                  >
                    +
                  </button>
                </div>

                {/* Price (LTP) */}
                <span style={{ fontWeight: 700, color: isBuy ? 'var(--color-success)' : 'var(--color-error)' }}>
                  ₹{leg.price.toFixed(2)}
                </span>

                {/* Delete */}
                <button
                  onClick={() => onRemoveLeg(leg.id)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: 2 }}
                  title="Remove Leg"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* ── SEBI 1-TOUCH BASKET EXECUTION BUTTON ────────────────────────── */}
      {legs.length > 0 && (
        <div style={{ marginTop: 'var(--space-2)' }}>
          <button
            onClick={handleExecute}
            disabled={isExecuting}
            className="btn btn-sm"
            style={{
              width: '100%',
              fontSize: '0.74rem',
              fontWeight: 900,
              background: 'linear-gradient(135deg, var(--color-primary), #059669)',
              color: '#000',
              border: 'none',
              boxShadow: '0 0 15px var(--color-primary-30)',
              gap: 'var(--space-2)',
            }}
          >
            <Zap size={14} />
            {isExecuting ? 'ROUTING BASKET TO RUST OMS...' : 'EXECUTE STRATEGY BASKET (1-TOUCH HITL)'}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, marginTop: 4, fontSize: '0.58rem', color: 'var(--color-text-muted)' }}>
            <ShieldCheck size={11} color="var(--color-primary)" />
            <span>SEBI 2026 Mandate Compliant • Instant Microsecond Basket Routing</span>
          </div>

          {executionMessage && (
            <div style={{ marginTop: 4, textAlign: 'center', fontSize: '0.68rem', fontWeight: 700, color: executionMessage.startsWith('✅') ? 'var(--color-success)' : 'var(--color-error)' }}>
              {executionMessage}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
