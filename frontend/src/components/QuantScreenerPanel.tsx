import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Filter, ArrowUpDown, ChevronDown, ChevronUp, Zap, Activity } from 'lucide-react';

interface ScreenerItem {
  ticker: string;
  compositeScore: number;
  momentumZ: number;
  relativeStrengthVsNifty: number;
  liquidityScore: number;
  oiSignal: 'LONG_BUILDUP' | 'SHORT_BUILDUP' | 'SHORT_COVERING' | 'LONG_UNWINDING' | 'NEUTRAL';
  recommendation: 'STRONG_BUY' | 'BUY' | 'WATCH' | 'AVOID';
  rationale: string;
}

const SAMPLE_SCREENER_DATA: ScreenerItem[] = [
  {
    ticker: 'TCS',
    compositeScore: 0.82,
    momentumZ: 2.15,
    relativeStrengthVsNifty: 4.8,
    liquidityScore: 0.95,
    oiSignal: 'LONG_BUILDUP',
    recommendation: 'STRONG_BUY',
    rationale: 'Heavy institutional volume expansion (+180% 20d avg). Massive open interest accretion with sustained price breakout.',
  },
  {
    ticker: 'HDFCBANK',
    compositeScore: 0.74,
    momentumZ: 1.80,
    relativeStrengthVsNifty: 3.2,
    liquidityScore: 0.98,
    oiSignal: 'LONG_BUILDUP',
    recommendation: 'STRONG_BUY',
    rationale: 'DII net buying concentration. Clean bounce from key daily support level with favorable risk-reward.',
  },
  {
    ticker: 'INFY',
    compositeScore: 0.61,
    momentumZ: 1.25,
    relativeStrengthVsNifty: 2.1,
    liquidityScore: 0.92,
    oiSignal: 'SHORT_COVERING',
    recommendation: 'BUY',
    rationale: 'Bears unwinding near 52-week median. Positive relative strength divergence vs IT index.',
  },
  {
    ticker: 'ICICIBANK',
    compositeScore: 0.15,
    momentumZ: 0.30,
    relativeStrengthVsNifty: 0.4,
    liquidityScore: 0.94,
    oiSignal: 'NEUTRAL',
    recommendation: 'WATCH',
    rationale: 'Consolidating in a tight intraday Bollinger Band squeeze. Awaiting institutional volume trigger.',
  },
  {
    ticker: 'TATAMOTORS',
    compositeScore: -0.45,
    momentumZ: -1.10,
    relativeStrengthVsNifty: -2.8,
    liquidityScore: 0.88,
    oiSignal: 'LONG_UNWINDING',
    recommendation: 'AVOID',
    rationale: 'Long liquidation underway after quarterly margins lagged consensus expectations.',
  },
  {
    ticker: 'ADANIENT',
    compositeScore: -0.68,
    momentumZ: -1.95,
    relativeStrengthVsNifty: -4.5,
    liquidityScore: 0.85,
    oiSignal: 'SHORT_BUILDUP',
    recommendation: 'AVOID',
    rationale: 'Aggressive aggressive derivatives short positioning. High beta exposure amplifying downward momentum.',
  },
];

export function QuantScreenerPanel() {
  const [data] = useState<ScreenerItem[]>(SAMPLE_SCREENER_DATA);
  const [expandedTicker, setExpandedTicker] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'score' | 'momentum' | 'alpha'>('score');
  const [isScanning, setIsScanning] = useState(false);

  const handleScan = () => {
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
    }, 900);
  };

  const sortedData = [...data].sort((a, b) => {
    if (sortBy === 'score') return b.compositeScore - a.compositeScore;
    if (sortBy === 'momentum') return b.momentumZ - a.momentumZ;
    return b.relativeStrengthVsNifty - a.relativeStrengthVsNifty;
  });

  const getOiBadge = (signal: string) => {
    switch (signal) {
      case 'LONG_BUILDUP':
        return <span className="badge badge-success">LONG BUILDUP</span>;
      case 'SHORT_BUILDUP':
        return <span className="badge badge-error">SHORT BUILDUP</span>;
      case 'SHORT_COVERING':
        return <span className="badge badge-primary">SHORT COVER</span>;
      case 'LONG_UNWINDING':
        return <span className="badge badge-warning">LONG UNWIND</span>;
      default:
        return <span className="badge">NEUTRAL</span>;
    }
  };

  const getActionBadge = (rec: string) => {
    if (rec === 'STRONG_BUY') return <span className="badge badge-success">STRONG BUY</span>;
    if (rec === 'BUY') return <span className="badge badge-primary">BUY</span>;
    if (rec === 'WATCH') return <span className="badge badge-warning">WATCH</span>;
    return <span className="badge badge-error">AVOID</span>;
  };

  return (
    <div className="glass-panel" style={{ padding: 'var(--space-6)' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div style={{
            width: 34, height: 34, borderRadius: 'var(--radius-md)',
            background: 'var(--color-primary-10)', border: '1px solid var(--color-primary-20)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)'
          }}>
            <Filter size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--color-text-primary)', letterSpacing: '-0.02em' }}>
              NSE/BSE QUANTUM ALPHA SCREENER
            </h3>
            <p style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
              Cross-Sectional Z-Scores • F&O Open Interest Buildup Metrics
            </p>
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <button
            onClick={() => setSortBy(sortBy === 'score' ? 'momentum' : (sortBy === 'momentum' ? 'alpha' : 'score'))}
            className="btn btn-sm btn-ghost"
            style={{ fontSize: '0.70rem' }}
          >
            <ArrowUpDown size={11} />
            Sort: {sortBy.toUpperCase()}
          </button>
          <button
            onClick={handleScan}
            disabled={isScanning}
            className="btn btn-sm btn-primary"
            style={{ fontSize: '0.70rem' }}
          >
            <Zap size={11} className={isScanning ? 'animate-pulse' : ''} />
            {isScanning ? 'SCANNING UNIVERSE...' : 'SCAN UNIVERSE'}
          </button>
        </div>
      </div>

      {/* Screener Table */}
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Score</th>
              <th>Mom. Z</th>
              <th>vs Nifty 50</th>
              <th>Liquidity</th>
              <th>OI Buildup</th>
              <th>Action</th>
              <th style={{ width: 30 }}></th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((item) => {
              const isExpanded = expandedTicker === item.ticker;
              const isBullish = item.compositeScore >= 0.5;
              const isBearish = item.compositeScore <= -0.4;

              return (
                <tr
                  key={item.ticker}
                  onClick={() => setExpandedTicker(isExpanded ? null : item.ticker)}
                  style={{
                    cursor: 'pointer',
                    background: isExpanded ? 'var(--color-bg-hover)' : 'transparent',
                    borderLeft: isBullish ? '2px solid var(--color-success)' : (isBearish ? '2px solid var(--color-error)' : 'none'),
                  }}
                >
                  <td style={{ fontWeight: 700, color: 'var(--color-text-primary)' }}>
                    {item.ticker}
                  </td>
                  <td style={{
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    color: item.compositeScore > 0 ? 'var(--color-success)' : 'var(--color-error)'
                  }}>
                    {item.compositeScore > 0 ? `+${item.compositeScore.toFixed(2)}` : item.compositeScore.toFixed(2)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>
                    {item.momentumZ > 0 ? `+${item.momentumZ.toFixed(2)}` : item.momentumZ.toFixed(2)}σ
                  </td>
                  <td style={{
                    fontFamily: 'var(--font-mono)',
                    color: item.relativeStrengthVsNifty >= 0 ? 'var(--color-success)' : 'var(--color-error)'
                  }}>
                    {item.relativeStrengthVsNifty >= 0 ? `+${item.relativeStrengthVsNifty.toFixed(1)}%` : `${item.relativeStrengthVsNifty.toFixed(1)}%`}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>
                    {(item.liquidityScore * 100).toFixed(0)}%
                  </td>
                  <td>
                    {getOiBadge(item.oiSignal)}
                  </td>
                  <td>
                    {getActionBadge(item.recommendation)}
                  </td>
                  <td style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>
                    {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Expanded Rationale Drawer */}
      <AnimatePresence>
        {expandedTicker && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{
              marginTop: 'var(--space-3)',
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-bg-secondary)',
              border: '1px dashed var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
            }}
          >
            <Activity size={14} color="var(--color-primary)" style={{ flexShrink: 0 }} />
            <p style={{ fontSize: '0.74rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              <strong style={{ color: 'var(--color-text-primary)' }}>{expandedTicker} Institutional Setup: </strong>
              {data.find(d => d.ticker === expandedTicker)?.rationale}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
