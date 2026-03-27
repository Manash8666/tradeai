import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { StatusCard }            from '../components/StatusCard';
import { ComplianceBadge }       from '../components/ComplianceBadge';
import { NLP_Agent_Feed }        from '../components/NLP_Agent_Feed';
import { BacktestRunner }        from '../components/BacktestRunner';
import { OptionsHeatmap }        from '../components/OptionsHeatmap';
import { OptionsSimulator }      from '../components/OptionsSimulator';
import { IndianExpiryMatrix }    from '../components/IndianExpiryMatrix';
import { RLVisualizer }          from '../components/RLVisualizer';
import { QuantumSpanVisualizer } from '../components/QuantumSpanVisualizer';
import { GIFTNiftyGapVisualizer} from '../components/GIFTNiftyGapVisualizer';
import { SEBI1TouchAuth }        from '../components/SEBI1TouchAuth';
import { SEBIKillSwitch }        from '../components/SEBIKillSwitch';
import { GreedCircuitBreaker }   from '../components/GreedCircuitBreaker';
import { ManipulationAlertsList} from '../components/ManipulationAlertsList';
import { MultiTimeframeGauge }   from '../components/MultiTimeframeGauge';
import { useComplianceStatus }   from '../hooks/useComplianceStatus';

interface HealthData {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}

const SECTION_GAP = { marginBottom: 'var(--space-6)' };

export function Dashboard() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<Date>(new Date());

  const fetchHealth = async () => {
    try {
      const r = await axios.get<HealthData>('/api/health');
      setHealth(r.data);
      setError(null);
      setLastFetch(new Date());
    } catch {
      setError('Backend unreachable');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const t = setInterval(fetchHealth, 30_000);
    return () => clearInterval(t);
  }, []);

  const { data: complianceChecks = [] } = useComplianceStatus();

  /* ─── SECTION DIVIDER HELPER ─── */
  const SectionLabel = ({ label }: { label: string }) => (
    <p style={{
      fontSize: '0.65rem',
      fontWeight: 700,
      letterSpacing: '0.14em',
      textTransform: 'uppercase',
      color: 'var(--color-text-muted)',
      fontFamily: 'var(--font-mono)',
      marginBottom: 'var(--space-3)',
    }}>{label}</p>
  );

  return (
    <div style={{
      padding: 'var(--space-8)',
      maxWidth: 1280,
      margin: '0 auto',
    }}>

      {/* ── HERO BLOCK ───────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          borderRadius: 'var(--radius-xl)',
          overflow: 'hidden',
          border: '1px solid var(--color-border)',
          background: 'var(--color-bg-secondary)',
          position: 'relative',
          marginBottom: 'var(--space-8)',
          padding: '80px var(--space-8) 48px',
          textAlign: 'center',
          transition: 'background var(--transition-slow)',
        }}
      >
        <div className="hero-beam" />
        {[
          { left: '8%',  height: '80px',  duration: '3s',   delay: '0s'   },
          { left: '18%', height: '120px', duration: '4.5s', delay: '1.2s' },
          { left: '32%', height: '60px',  duration: '3.8s', delay: '2.5s' },
          { left: '68%', height: '100px', duration: '4s',   delay: '0.8s' },
          { left: '82%', height: '70px',  duration: '3.5s', delay: '1.8s' },
          { left: '92%', height: '90px',  duration: '4.2s', delay: '3s'   },
        ].map((s, i) => (
          <div key={`s${i}`} className="hero-stream" style={{ left: s.left, height: s.height, animationDuration: s.duration, animationDelay: s.delay }} />
        ))}

        <div style={{ position: 'relative', zIndex: 10 }}>
          <h1 className="hero-text-glitch" data-text="INSTITUTIONAL AI CORE" style={{ fontSize: 'clamp(1.8rem, 4vw, 3rem)', fontWeight: 900, letterSpacing: '-0.04em', color: 'var(--color-text-primary)', marginBottom: 'var(--space-3)' }}>
            INSTITUTIONAL AI CORE
          </h1>
          <p className="hero-tag-line" style={{ fontSize: '0.9rem', color: 'var(--color-primary)', fontFamily: 'var(--font-mono)', display: 'inline-block' }}>
            SEBI Compliant Execution • Zero-Latency
          </p>
        </div>
      </motion.div>

      {/* ── SEBI COMPLIANCE CONTROLS (Phase 13–14) ──────────────────────── */}
      <SectionLabel label="SEBI 2026 Compliance Controls" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginBottom: 'var(--space-8)' }}>
        <SEBIKillSwitch />
        <SEBI1TouchAuth />
      </div>

      {/* ── STATUS KPI CARDS ─────────────────────────────────────────────── */}
      <SectionLabel label="System Status" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
        <StatusCard title="Backend Status"   value={loading ? 'Loading…' : health ? 'Online'  : 'Offline'}       subtitle={health ? `v${health.version}` : error || undefined} status={loading ? 'warning' : health ? 'healthy' : 'error'} icon="🖥️" delay={0.1} />
        <StatusCard title="Environment"      value={health?.environment || '—'}                                   subtitle={health?.service}                                    status="neutral"                                              icon="⚙️" delay={0.2} />
        <StatusCard title="Last Check"       value={lastFetch.toLocaleTimeString()}                              subtitle="Auto-refresh: 30s"                                  status="neutral"                                              icon="🕐" delay={0.3} />
        <StatusCard title="Database"         value={health ? 'Connected' : 'Unknown'}                            subtitle="PostgreSQL 15"                                      status={health ? 'healthy' : 'warning'}                      icon="🗄️" delay={0.4} />
      </div>

      {/* ── GREED CIRCUIT BREAKER (Phase 15) ─────────────────────────────── */}
      <SectionLabel label="Behavioral Risk · Daily P&L Lock" />
      <div style={SECTION_GAP}>
        <GreedCircuitBreaker />
      </div>

      {/* ── 0DTE INDIAN EXPIRY MATRIX (Phase 7) ───────────────────────────── */}
      <SectionLabel label="NSE / BSE 0DTE Expiry Matrix" />
      <div style={SECTION_GAP}>
        <IndianExpiryMatrix />
      </div>

      {/* ── AI ENGINES ───────────────────────────────────────────────────── */}
      <SectionLabel label="AI Intelligence Layer" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
        <RLVisualizer />
        <QuantumSpanVisualizer />
        <GIFTNiftyGapVisualizer />
      </div>

      {/* ── ANALYSIS GRID ─────────────────────────────────────────────────── */}
      <SectionLabel label="Market Intelligence" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 'var(--space-5)', marginBottom: 'var(--space-8)' }}>
        <NLP_Agent_Feed />
        <MultiTimeframeGauge />
        <ManipulationAlertsList />
      </div>

      {/* ── TRADING TOOLS ─────────────────────────────────────────────────── */}
      <SectionLabel label="Trading Tools" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 'var(--space-5)', marginBottom: 'var(--space-8)' }}>
        <BacktestRunner />
        <OptionsSimulator />
      </div>

      {/* ── OPTIONS HEATMAP ───────────────────────────────────────────────── */}
      <SectionLabel label="Options Heatmap · NIFTY 50" />
      <div style={SECTION_GAP}>
        <OptionsHeatmap symbol="NIFTY50" />
      </div>

      {/* ── COMPLIANCE + TECH STACK ───────────────────────────────────────── */}
      <SectionLabel label="Compliance & Platform" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-5)', marginBottom: 'var(--space-8)' }}>
        <ComplianceBadge checks={complianceChecks} />

        <motion.div
          className="glass-panel"
          style={{ padding: 'var(--space-5)' }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.7 }}
        >
          <h3 style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: 'var(--space-4)' }}>
            Tech Stack
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {[
              { label: 'Backend',  value: 'FastAPI + Python 3.11',  icon: '🐍' },
              { label: 'Frontend', value: 'React 19 + TypeScript',  icon: '⚛️' },
              { label: 'Database', value: 'ClickHouse + PostgreSQL', icon: '🗃️' },
              { label: 'Cache',    value: 'Redis 7',                icon: '⚡' },
              { label: 'HFT Core', value: 'Rust + PyO3 (<0.05ms)',   icon: '🚀' },
              { label: 'DevOps',   value: 'Docker + GitHub Actions', icon: '🐳' },
            ].map((item, i) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 + i * 0.07 }}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: 'var(--space-2) var(--space-3)',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--color-bg-hover)',
                  border: '1px solid var(--color-border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span style={{ fontSize: '0.85rem' }}>{item.icon}</span>
                  <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)' }}>{item.label}</span>
                </div>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {item.value}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Footer spacing */}
      <div style={{ height: 'var(--space-12)' }} />
    </div>
  );
}
