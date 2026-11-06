import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Brain,
  ShieldCheck,
  RefreshCw,
  Scale
} from 'lucide-react';

interface CouncilVerdict {
  ticker: string;
  direction: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  bull_thesis: string;
  bear_thesis: string;
  final_rationale: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  suggested_position_size_pct: number;
  ist_timestamp: string;
}

const SAMPLE_VERDICTS: Record<string, CouncilVerdict> = {
  NIFTY50: {
    ticker: 'NIFTY50',
    direction: 'BUY',
    confidence: 0.84,
    bull_thesis: 'Institutional accumulation dominant (+₹1,850 Cr net DII inflow). Price sustaining above 24,500 VWAP with 0DTE gamma skew targeting 24,650.',
    bear_thesis: 'Elevated Brent crude ($82/bbl) applying modest pressure on USD/INR. Resistance heavy at 24,700 Call strike.',
    final_rationale: 'Deliberative council consensus: Bull thesis (+0.82) dominates Bear risk (-0.35). Entering momentum swing long.',
    risk_level: 'LOW',
    suggested_position_size_pct: 7.5,
    ist_timestamp: '11:15:30 IST',
  },
  BANKNIFTY: {
    ticker: 'BANKNIFTY',
    direction: 'SELL',
    confidence: 0.78,
    bull_thesis: 'PSU banks showing resilient asset quality metrics and low credit cost baselines.',
    bear_thesis: 'Severe 5m overbought spike (RSI: 78.2). FIIs sold -₹450 Cr in Private Bank index futures.',
    final_rationale: 'Mean-reversion trigger active. Council recommends shorting intraday exhaustion back to VWAP support.',
    risk_level: 'MEDIUM',
    suggested_position_size_pct: 5.0,
    ist_timestamp: '11:16:02 IST',
  },
  RELIANCE: {
    ticker: 'RELIANCE',
    direction: 'HOLD',
    confidence: 0.52,
    bull_thesis: 'Retail and telecom earnings visibility providing long-term compound growth floor.',
    bear_thesis: 'Refining margins (GRMs) compressed. Stock oscillating within narrow 52-week midpoint equilibrium.',
    final_rationale: 'Equilibrium posture. Risk-reward does not offer sufficient statistical edge; awaiting breakout.',
    risk_level: 'LOW',
    suggested_position_size_pct: 0.0,
    ist_timestamp: '11:16:45 IST',
  },
};

export function AnalystCouncilPanel() {
  const [selectedTicker, setSelectedTicker] = useState<'NIFTY50' | 'BANKNIFTY' | 'RELIANCE'>('NIFTY50');
  const [isDeliberating, setIsDeliberating] = useState(false);

  const verdict = SAMPLE_VERDICTS[selectedTicker];

  const handleTriggerDeliberation = () => {
    setIsDeliberating(true);
    setTimeout(() => {
      setIsDeliberating(false);
    }, 1200);
  };

  const getDirectionBadge = (dir: string) => {
    if (dir === 'BUY') return <span className="badge badge-success"><TrendingUp size={11} /> BUY SIGNAL</span>;
    if (dir === 'SELL') return <span className="badge badge-error"><TrendingDown size={11} /> SELL / HEDGE</span>;
    return <span className="badge badge-warning"><Scale size={11} /> HOLD / NEUTRAL</span>;
  };

  const getRiskBadge = (risk: string) => {
    if (risk === 'LOW') return <span className="badge badge-success">RISK: LOW</span>;
    if (risk === 'MEDIUM') return <span className="badge badge-warning">RISK: MEDIUM</span>;
    return <span className="badge badge-error">RISK: HIGH</span>;
  };

  return (
    <div className="glass-panel" style={{ padding: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div style={{
            width: 34, height: 34, borderRadius: 'var(--radius-md)',
            background: 'var(--color-primary-10)', border: '1px solid var(--color-primary-20)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)'
          }}>
            <Brain size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--color-text-primary)', letterSpacing: '-0.02em' }}>
              INDIAN QUANT ANALYST COUNCIL
            </h3>
            <p style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
              6-Agent Hierarchical Consensus • SEBI Advisory Safe-Harbor
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          {(['NIFTY50', 'BANKNIFTY', 'RELIANCE'] as const).map(t => (
            <button
              key={t}
              onClick={() => { setSelectedTicker(t); handleTriggerDeliberation(); }}
              className={`btn btn-sm ${selectedTicker === t ? 'btn-primary' : 'btn-ghost'}`}
              style={{ fontSize: '0.70rem', padding: 'var(--space-1) var(--space-3)' }}
            >
              {t}
            </button>
          ))}
          <button
            onClick={handleTriggerDeliberation}
            className="btn btn-sm btn-ghost"
            title="Re-run Multi-Agent Deliberation"
            style={{ padding: 'var(--space-1) var(--space-2)' }}
          >
            <RefreshCw size={12} className={isDeliberating ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* 6 Specialist Agent Status Chips */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: 'var(--space-2)',
        marginBottom: 'var(--space-5)',
        padding: 'var(--space-3)',
        borderRadius: 'var(--radius-md)',
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border-subtle)',
      }}>
        {[
          { label: 'Fundamentals', status: 'ALIGNED', color: 'var(--color-success)' },
          { label: 'Sentiment', status: 'BULLISH', color: 'var(--color-success)' },
          { label: 'Technicals', status: 'VWAP+', color: 'var(--color-primary)' },
          { label: 'FII / DII Flow', status: 'INFLOW', color: 'var(--color-success)' },
          { label: 'Bull Case', status: '+0.82', color: 'var(--color-success)' },
          { label: 'Bear Defense', status: '-0.35', color: 'var(--color-warning)' },
        ].map((agent, idx) => (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {agent.label}
            </span>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: agent.color, fontFamily: 'var(--font-mono)' }}>
              {isDeliberating ? '...' : agent.status}
            </span>
          </div>
        ))}
      </div>

      {/* Verdict Panel */}
      <AnimatePresence mode="wait">
        {isDeliberating ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              padding: 'var(--space-8)',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 'var(--space-3)',
            }}
          >
            <RefreshCw size={24} className="animate-spin" color="var(--color-primary)" />
            <p style={{ fontSize: '0.80rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>
              ADVERSARIAL COUNCIL DELIBERATING ON {selectedTicker}...
            </p>
          </motion.div>
        ) : (
          <motion.div
            key="verdict"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}
          >
            {/* Verdict Header Ribbon */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-bg-hover)',
              border: '1px solid var(--color-border)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                {getDirectionBadge(verdict.direction)}
                {getRiskBadge(verdict.risk_level)}
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                  Size: {verdict.suggested_position_size_pct}% Cap
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>Confidence:</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--color-primary)', fontFamily: 'var(--font-mono)' }}>
                  {(verdict.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Confidence Progress Bar */}
            <div style={{ width: '100%', height: 4, background: 'var(--color-border-subtle)', borderRadius: 2, overflow: 'hidden' }}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${verdict.confidence * 100}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                style={{ height: '100%', background: 'var(--color-primary)' }}
              />
            </div>

            {/* Bull vs Bear Adversarial Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-3)' }}>
              {/* Bull Case */}
              <div style={{
                padding: 'var(--space-4)',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(0, 255, 136, 0.04)',
                borderLeft: '3px solid var(--color-success)',
                border: '1px solid var(--color-border-subtle)',
                borderLeftWidth: 3,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                  <TrendingUp size={14} color="var(--color-success)" />
                  <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-success)', textTransform: 'uppercase' }}>
                    Affirmative Thesis (Bull)
                  </span>
                </div>
                <p style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                  {verdict.bull_thesis}
                </p>
              </div>

              {/* Bear Case */}
              <div style={{
                padding: 'var(--space-4)',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(255, 48, 92, 0.04)',
                borderLeft: '3px solid var(--color-error)',
                border: '1px solid var(--color-border-subtle)',
                borderLeftWidth: 3,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                  <TrendingDown size={14} color="var(--color-error)" />
                  <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-error)', textTransform: 'uppercase' }}>
                    Adversarial Risks (Bear)
                  </span>
                </div>
                <p style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                  {verdict.bear_thesis}
                </p>
              </div>
            </div>

            {/* Consensus Rationale */}
            <div style={{
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-bg-secondary)',
              border: '1px dashed var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
            }}>
              <ShieldCheck size={16} color="var(--color-primary)" style={{ flexShrink: 0 }} />
              <p style={{ fontSize: '0.74rem', color: 'var(--color-text-primary)', fontStyle: 'italic', margin: 0 }}>
                {verdict.final_rationale}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
