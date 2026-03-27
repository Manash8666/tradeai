import { useState, useEffect } from 'react';
import { Activity, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { motion } from 'framer-motion';

interface Signal {
  symbol: string;
  model_id: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  timestamp: string | null;
}

export function SignalsPanel() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSignals = async () => {
    try {
      const response = await fetch('http://localhost:8000/signals/active');
      if (!response.ok) throw new Error('Failed to fetch signals');
      const data = await response.json();
      setSignals(data);
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div style={{ color: 'var(--color-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.78rem', animation: 'pulse 2s ease-in-out infinite', padding: 'var(--space-4)' }}>
      Initializing AI Models…
    </div>
  );

  if (error) return (
    <div className="badge badge-error" style={{ padding: 'var(--space-3) var(--space-4)', fontSize: '0.78rem', borderRadius: 'var(--radius-md)' }}>
      Connection Error: {error}
    </div>
  );

  if (signals.length === 0) return (
    <div style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.78rem', padding: 'var(--space-4)' }}>
      No active signals
    </div>
  );

  const signalMeta = {
    BUY:  { color: 'var(--color-success)', barColor: 'var(--color-success)', Icon: TrendingUp },
    SELL: { color: 'var(--color-error)',   barColor: 'var(--color-error)',   Icon: TrendingDown },
    HOLD: { color: 'var(--color-primary)', barColor: 'var(--color-primary)', Icon: Minus },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      {signals.map((sig, idx) => {
        const meta = signalMeta[sig.signal] || signalMeta.HOLD;
        const { color, barColor, Icon } = meta;
        const pct = Math.round(sig.confidence * 100);

        return (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.08 }}
            style={{
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-3) var(--space-4)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <Activity size={14} style={{ color: 'var(--color-primary)', flexShrink: 0 }} />
                <span style={{ fontWeight: 700, color: 'var(--color-text-primary)', fontSize: '0.85rem' }}>{sig.symbol}</span>
                <span style={{
                  fontSize: '0.65rem', fontFamily: 'var(--font-mono)',
                  color: 'var(--color-text-muted)', background: 'var(--color-bg-hover)',
                  padding: '1px 6px', borderRadius: 'var(--radius-sm)',
                }}>
                  {sig.model_id}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontWeight: 800, color, fontSize: '0.8rem', letterSpacing: '0.05em' }}>
                <Icon size={14} />
                {sig.signal}
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)', marginBottom: 4 }}>
                <span>Confidence</span>
                <span style={{ color }}>{pct}%</span>
              </div>
              <div style={{ height: 4, background: 'var(--color-border-subtle)', borderRadius: 999, overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  style={{ height: '100%', background: barColor, borderRadius: 999 }}
                />
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
