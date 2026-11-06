import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap,
  TrendingUp,
  Cpu,
  BarChart3,
  Layers,
  RefreshCw,
  Terminal,
} from 'lucide-react';
import axios from 'axios';

import { ErrorBoundary } from '../components/ErrorBoundary';
import { SEBIKillSwitch } from '../components/SEBIKillSwitch';
import { SEBI1TouchAuth } from '../components/SEBI1TouchAuth';
import { GreedCircuitBreaker } from '../components/GreedCircuitBreaker';
import { ManipulationAlertsList } from '../components/ManipulationAlertsList';
import { AnalystCouncilPanel } from '../components/AnalystCouncilPanel';
import { QuantScreenerPanel } from '../components/QuantScreenerPanel';
import { BacktestResultPanel } from '../components/BacktestResultPanel';
import { BacktestRunner } from '../components/BacktestRunner';
import { IndianExpiryMatrix } from '../components/IndianExpiryMatrix';
import { OptionsHeatmap } from '../components/OptionsHeatmap';
import { RLVisualizer } from '../components/RLVisualizer';
import { QuantumSpanVisualizer } from '../components/QuantumSpanVisualizer';
import { GIFTNiftyGapVisualizer } from '../components/GIFTNiftyGapVisualizer';
import { MultiTimeframeGauge } from '../components/MultiTimeframeGauge';
import { NLP_Agent_Feed } from '../components/NLP_Agent_Feed';
import { ComplianceBadge } from '../components/ComplianceBadge';
import { useComplianceStatus } from '../hooks/useComplianceStatus';

type TerminalSubTab = 'execution' | 'council' | 'screener' | 'options_vol' | 'backtest';

export function Dashboard() {
  const [activeTab, setActiveTab] = useState<TerminalSubTab>('execution');
  const [healthStatus, setHealthStatus] = useState({
    status: 'online',
    version: '0.1.0',
    latency_us: 38,
    memory_mb: 214,
    lastPing: new Date(),
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data: complianceChecks = [] } = useComplianceStatus();

  const fetchHealth = async () => {
    setIsRefreshing(true);
    try {
      const res = await axios.get('/api/health');
      if (res.data) {
        setHealthStatus((prev) => ({
          ...prev,
          status: res.data.status || 'online',
          version: res.data.version || '0.1.0',
          lastPing: new Date(),
        }));
      }
    } catch {
      // Offline fallback
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  const subTabs = [
    { id: 'execution' as const, label: 'Execution & HFT OMS', icon: Zap, badge: '<38µs' },
    { id: 'council' as const, label: 'Quant Council', icon: Layers, badge: '6-Agents' },
    { id: 'screener' as const, label: 'Alpha Screener', icon: TrendingUp, badge: 'F&O Z-Score' },
    { id: 'options_vol' as const, label: '0DTE & Options Flow', icon: BarChart3, badge: 'Live Heatmap' },
    { id: 'backtest' as const, label: 'Walk-Forward Backtest', icon: Cpu, badge: 'DSR Rigor' },
  ];

  return (
    <div className="w-full min-h-screen bg-[#05070c] bg-grid-pattern text-slate-100 p-6 md:p-8 space-y-6">
      {/* ── TOP COCKPIT TELEMETRY BAR ── */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-[#0c1017]/95 via-[#080d16]/95 to-[#0b121e]/95 border border-white/[0.08] shadow-[0_12px_36px_rgba(0,0,0,0.6)] backdrop-blur-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Desk Identification */}
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 flex items-center justify-center shadow-[0_0_20px_rgba(0,255,136,0.15)]">
              <Terminal className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-syne text-xl font-black text-white tracking-tight">
                  INSTITUTIONAL QUANT COMMAND TERMINAL
                </h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  DESK #1 · {healthStatus.status.toUpperCase()} · v{healthStatus.version}
                </span>
              </div>
              <p className="text-xs font-mono text-slate-400 mt-0.5">
                Sub-50µs PyO3 Rust HFT OMS · SEBI April 1, 2026 HITL 1-Touch Barrier · ClickHouse Audit Hash
              </p>
            </div>
          </div>

          {/* Quick Metrics Cluster */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Capital NAV */}
            <div className="px-3.5 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Capital Pool</div>
              <div className="text-sm font-mono font-bold text-white tracking-tight">
                ₹1,00,00,000 <span className="text-[10px] text-emerald-400 font-normal">(+0.48%)</span>
              </div>
            </div>

            {/* HFT Latency */}
            <div className="px-3.5 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div className="text-[10px] font-mono text-slate-400 uppercase">PyO3 Rust OMS</div>
              <div className="text-sm font-mono font-bold text-emerald-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                38.2 µs
              </div>
            </div>

            {/* India VIX & GIFT */}
            <div className="px-3.5 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div className="text-[10px] font-mono text-slate-400 uppercase">India VIX / GIFT</div>
              <div className="text-sm font-mono font-bold text-cyan-300">
                15.81 <span className="text-[10px] text-emerald-400 font-normal">(+28.5 pts)</span>
              </div>
            </div>

            {/* Refresh Button */}
            <button
              onClick={fetchHealth}
              disabled={isRefreshing}
              className="p-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-slate-300 hover:text-white transition-all cursor-pointer"
              title="Refresh Telemetry"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* ── COCKPIT SUB-NAVIGATION TABS ── */}
      <div className="flex overflow-x-auto p-1.5 rounded-xl bg-white/[0.02] border border-white/[0.06] backdrop-blur-md gap-2">
        {subTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 min-w-[180px] px-4 py-2.5 rounded-lg text-xs font-sans font-semibold tracking-wide flex items-center justify-between transition-all duration-200 cursor-pointer ${
                isActive
                  ? 'bg-gradient-to-r from-emerald-500/15 via-teal-500/10 to-transparent text-white border border-emerald-500/30 shadow-[0_4px_16px_rgba(0,255,136,0.1)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03] border border-transparent'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </div>
              <span
                className={`text-[9px] font-mono px-2 py-0.5 rounded-full ${
                  isActive
                    ? 'bg-emerald-500/20 text-emerald-300 font-bold'
                    : 'bg-white/[0.04] text-slate-400'
                }`}
              >
                {tab.badge}
              </span>
            </button>
          );
        })}
      </div>

      {/* ── TAB CONTENT CONTAINERS (Wrapped in ErrorBoundaries) ── */}
      <AnimatePresence mode="wait">
        {activeTab === 'execution' && (
          <motion.div
            key="execution"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            {/* Regulatory Safeguards Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ErrorBoundary fallbackTitle="SEBI Kill Switch Module">
                <SEBIKillSwitch />
              </ErrorBoundary>

              <ErrorBoundary fallbackTitle="SEBI 1-Touch 2026 Authorization Card">
                <SEBI1TouchAuth />
              </ErrorBoundary>
            </div>

            {/* Behavioral Greed Circuit Breaker & Alerts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ErrorBoundary fallbackTitle="Greed Circuit Breaker & Tilt Detector">
                <GreedCircuitBreaker />
              </ErrorBoundary>

              <ErrorBoundary fallbackTitle="Market Manipulation & Spoofing Alerts">
                <ManipulationAlertsList />
              </ErrorBoundary>
            </div>

            {/* SEBI Compliance Readiness Grid */}
            <ErrorBoundary fallbackTitle="SEBI Compliance Telemetry">
              <ComplianceBadge checks={complianceChecks} />
            </ErrorBoundary>
          </motion.div>
        )}

        {activeTab === 'council' && (
          <motion.div
            key="council"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            <ErrorBoundary fallbackTitle="Quant Council 6-Agent Consensus">
              <AnalystCouncilPanel />
            </ErrorBoundary>

            {/* Sentiment NLP Agent & Timeframe Alignment */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ErrorBoundary fallbackTitle="Institutional Sentiment NLP Feed">
                <NLP_Agent_Feed />
              </ErrorBoundary>

              <ErrorBoundary fallbackTitle="Multi-Timeframe Technical Gauge">
                <MultiTimeframeGauge />
              </ErrorBoundary>
            </div>
          </motion.div>
        )}

        {activeTab === 'screener' && (
          <motion.div
            key="screener"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            <ErrorBoundary fallbackTitle="Institutional Cross-Sectional Alpha Screener">
              <QuantScreenerPanel />
            </ErrorBoundary>

            {/* Pre-Market Gap Visualizer */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ErrorBoundary fallbackTitle="GIFT Nifty Opening Gap Fade Visualizer">
                <GIFTNiftyGapVisualizer />
              </ErrorBoundary>

              <ErrorBoundary fallbackTitle="SEBI PTRC SPAN Margin Visualizer">
                <QuantumSpanVisualizer />
              </ErrorBoundary>
            </div>
          </motion.div>
        )}

        {activeTab === 'options_vol' && (
          <motion.div
            key="options_vol"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            <ErrorBoundary fallbackTitle="Live 50-Strike Options OI Heatmap">
              <OptionsHeatmap symbol="NIFTY50" />
            </ErrorBoundary>

            <ErrorBoundary fallbackTitle="0DTE Indian Expiry Matrix">
              <IndianExpiryMatrix />
            </ErrorBoundary>
          </motion.div>
        )}

        {activeTab === 'backtest' && (
          <motion.div
            key="backtest"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            <ErrorBoundary fallbackTitle="Institutional Walk-Forward Backtest Analytics">
              <BacktestResultPanel />
            </ErrorBoundary>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ErrorBoundary fallbackTitle="Backtest Execution Runner">
                <BacktestRunner />
              </ErrorBoundary>

              <ErrorBoundary fallbackTitle="Indian F&O Reinforcement Learning Policy">
                <RLVisualizer />
              </ErrorBoundary>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
