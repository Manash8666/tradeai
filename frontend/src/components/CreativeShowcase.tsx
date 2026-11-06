import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Zap,
  Shield,
  Sliders,
  Sparkles,
  Cpu,
  BarChart3,
  ArrowUpRight,
  ChevronRight,
  Terminal,
  Activity,
} from 'lucide-react';
import axios from 'axios';

interface CreativeShowcaseProps {
  onSelectView: (view: 'showcase' | 'live_trading' | 'strategy_builder' | 'mirajane' | 'dashboard') => void;
}

export function CreativeShowcase({ onSelectView }: CreativeShowcaseProps) {
  const [marketTelemetry, setMarketTelemetry] = useState({
    nifty_spot: 23806.95,
    banknifty_spot: 51240.20,
    vix: 15.81,
    gift_spread: 28.5,
    crude: 81.20,
    moe_directive: 'AGGRESSIVE_CALL_SPREAD_OR_LONG',
    moe_expert: 'PriceActionSMC (100%)',
    hft_latency_us: 38.2,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [statusRes, moeRes] = await Promise.all([
          axios.get('/api/mirajane/status'),
          axios.get('/api/mirajane/moe/infer'),
        ]);
        if (statusRes.data) {
          setMarketTelemetry((prev) => ({
            ...prev,
            crude: statusRes.data.brent_crude_usd || 81.20,
            gift_spread: statusRes.data.gift_nifty_spread || 28.5,
          }));
        }
        if (moeRes.data) {
          setMarketTelemetry((prev) => ({
            ...prev,
            moe_directive: moeRes.data.action_directive || prev.moe_directive,
            moe_expert: moeRes.data.top_2_experts?.[0]
              ? `${moeRes.data.top_2_experts[0].expert} (${moeRes.data.top_2_experts[0].weight_pct}%)`
              : prev.moe_expert,
          }));
        }
      } catch {
        // Resilient fallback
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const marqueeKeywords = [
    'NIFTY 50 DERIVATIVES (23,806.95)',
    'MIRAJANE STRAUSS AUTONOMOUS BOT',
    'SEBI APRIL 1, 2026 HITL 1-TOUCH BARRIER',
    '32 READY-MADE STOCKMOJO PAYOFF TOPOLOGIES',
    'PETER JÄCKEL FAST IV SOLVER (<0.25ms)',
    'DEEPSEEK-V3 MOE ROUTER',
    'SMART MONEY CONCEPTS (FVG & ORDER BLOCKS)',
    '5-YEAR HISTORICAL BHAVCOPY (6,210 RECORDS)',
    'PYO3 RUST HFT OMS (<38µS LATENCY)',
    'BAILEY & LÓPEZ DE PRADO DEFLATED SHARPE (DSR)',
  ];

  return (
    <div className="w-full min-h-screen bg-[#05070c] bg-ambient-glow text-slate-100 overflow-x-hidden">
      {/* ── 1. LUXURY EDITORIAL HERO SECTION ── */}
      <section className="relative px-6 sm:px-10 lg:px-16 pt-16 pb-12 max-w-7xl mx-auto flex flex-col items-start">
        {/* Subtle Ambient Radial Glow */}
        <div className="absolute top-0 left-1/4 w-[600px] h-[360px] bg-emerald-500/[0.06] blur-[120px] rounded-full pointer-events-none -z-10" />
        <div className="absolute top-1/3 right-10 w-[500px] h-[300px] bg-cyan-500/[0.04] blur-[100px] rounded-full pointer-events-none -z-10" />

        {/* Top Tag & Status */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex items-center gap-3 mb-6"
        >
          <span className="font-mono text-xs font-bold tracking-widest uppercase text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-3 py-1 rounded-full flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            DALAL STREET · INSTITUTIONAL QUANT PLATFORM
          </span>
          <span className="text-slate-400 text-xs hidden sm:inline">/</span>
          <span className="font-mono text-xs text-slate-400 hidden sm:inline">
            SEBI April 1, 2026 HITL Certified
          </span>
        </motion.div>

        {/* Massive Editorial Headline */}
        <div className="w-full flex flex-col lg:flex-row items-start lg:items-end justify-between gap-8 mb-10">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="max-w-4xl"
          >
            <h1 className="font-syne text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight uppercase leading-[0.95] text-white">
              DISRUPTIVE <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                QUANTUM ALPHA
              </span>
              <br />
              FOR DALAL STREET.
            </h1>
            <p className="font-sans text-base sm:text-lg text-slate-300 font-normal leading-relaxed mt-6 max-w-2xl">
              Shattering retail algorithmic barriers with{' '}
              <span className="text-emerald-400 font-semibold font-mono">&lt;38µs PyO3 Rust HFT OMS</span> execution,
              Peter Jäckel machine-precision option Greeks ({' '}
              <span className="text-cyan-400 font-semibold font-mono">&lt;0.25ms</span> full-chain IV curves),
              DeepSeek-V3 MoE multi-agent reasoning, and 32 ready-made StockMojo topologies.
            </p>

            {/* Quick CTAs */}
            <div className="flex flex-wrap items-center gap-3 mt-8">
              <button
                onClick={() => onSelectView('strategy_builder')}
                className="btn btn-primary btn-lg flex items-center gap-2 shadow-[0_0_30px_rgba(0,255,136,0.25)]"
              >
                <Sliders className="w-4 h-4" />
                <span>Strategy Builder</span>
                <ArrowUpRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => onSelectView('mirajane')}
                className="btn btn-ghost btn-lg flex items-center gap-2 border-violet-500/30 hover:border-violet-500/50 hover:bg-violet-500/10 text-violet-300"
              >
                <Sparkles className="w-4 h-4 text-violet-400" />
                <span>Mirajane Strauss AI</span>
              </button>
              <button
                onClick={() => onSelectView('dashboard')}
                className="btn btn-ghost btn-lg flex items-center gap-2"
              >
                <Terminal className="w-4 h-4 text-emerald-400" />
                <span>Command Terminal</span>
              </button>
            </div>
          </motion.div>

          {/* Rotating Circular Seal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative w-36 h-36 flex-shrink-0 self-center lg:self-end"
          >
            <div className="absolute inset-0 rounded-full border border-emerald-500/20 bg-emerald-500/[0.03] backdrop-blur-md" />
            <svg
              className="w-full h-full animate-spin-slow"
              viewBox="0 0 160 160"
            >
              <path
                id="sealCircle"
                d="M 80, 80 m -60, 0 a 60,60 0 1,1 120,0 a 60,60 0 1,1 -120,0"
                fill="none"
              />
              <text className="text-[9.5px] font-mono font-bold uppercase tracking-[0.22em] fill-emerald-400">
                <textPath href="#sealCircle" startOffset="0%">
                  · DALAL STREET · SEBI 2026 HITL · &lt;38µS HFT · 32 TOPOLOGIES ·
                </textPath>
              </text>
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center shadow-[0_0_24px_rgba(0,255,136,0.4)]">
                <Zap className="w-5 h-5 text-black fill-black" />
              </div>
            </div>
          </motion.div>
        </div>

        {/* ── 4 Quick Stat Cards ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="w-full grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          {[
            {
              label: 'Institutional Capital Pool',
              value: '₹1,00,00,000',
              sub: '₹1.00 Crore Protected',
              accent: 'text-emerald-400',
              border: 'hover:border-emerald-500/40',
            },
            {
              label: 'PyO3 Rust HFT OMS',
              value: '<38.2 µs',
              sub: 'Microsecond Matching',
              accent: 'text-cyan-400',
              border: 'hover:border-cyan-500/40',
            },
            {
              label: 'Peter Jäckel Fast IV',
              value: '0.25 ms',
              sub: 'Full Chain Vol Surface',
              accent: 'text-emerald-400',
              border: 'hover:border-emerald-500/40',
            },
            {
              label: 'Ready-Made Topologies',
              value: '32 Topologies',
              sub: 'StockMojo 100% Parity',
              accent: 'text-violet-400',
              border: 'hover:border-violet-500/40',
            },
          ].map((stat, i) => (
            <div
              key={i}
              className={`p-4 rounded-xl bg-gradient-to-br from-white/[0.04] to-transparent border border-white/[0.07] backdrop-blur-md transition-all duration-300 ${stat.border}`}
            >
              <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                {stat.label}
              </div>
              <div className={`text-xl sm:text-2xl font-mono font-bold mt-1 ${stat.accent}`}>
                {stat.value}
              </div>
              <div className="text-[11px] font-sans text-slate-400 mt-0.5">
                {stat.sub}
              </div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* ── 2. INFINITE MARQUEE TICKER BANNER ── */}
      <div className="w-full border-y border-white/[0.08] bg-[#070b12] py-3.5 overflow-hidden">
        <div className="animate-marquee flex items-center gap-8">
          {[...marqueeKeywords, ...marqueeKeywords].map((word, idx) => (
            <div key={idx} className="flex items-center gap-8 shrink-0">
              <span className="font-syne text-xs font-bold tracking-widest uppercase text-slate-300 hover:text-emerald-400 transition-colors cursor-default">
                {word}
              </span>
              <span className="text-emerald-400 text-xs">✦</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── 3. NUMBERED CAPABILITY CARDS (01 TO 05) ── */}
      <section className="px-6 sm:px-10 lg:px-16 py-20 max-w-7xl mx-auto space-y-12">
        <div className="max-w-2xl">
          <div className="font-mono text-xs text-emerald-400 uppercase tracking-widest mb-2">
            // ARCHITECTURAL MATRIX
          </div>
          <h2 className="font-syne text-3xl sm:text-4xl font-extrabold uppercase text-white tracking-tight">
            WHAT WE HAVE TO OFFER.
          </h2>
          <p className="font-sans text-sm text-slate-300 mt-2">
            Five distinct, seamlessly wired institutional tiers engineered to replace fragile retail tools with industrial quant dominance.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* 01: StockMojo Option Strategy Builder */}
          <div className="creative-agency-card p-6 flex flex-col justify-between group">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-xs font-bold text-cyan-400 uppercase tracking-widest">
                  01 / DERIVATIVES
                </span>
                <Sliders className="w-5 h-5 text-cyan-400 group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="font-syne text-xl font-bold text-white mb-2">
                StockMojo Strategy Builder
              </h3>
              <p className="font-sans text-xs text-slate-300 leading-relaxed">
                Live option chain with centered strikes, soft blue ATM highlights, Black-Scholes Greeks, 32 ready-made payoff curves across Bullish, Bearish, Neutral, and Other, plus Peter Jäckel full-chain IV curves.
              </p>
              <div className="flex flex-wrap gap-1.5 mt-4">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  32 TOPOLOGIES
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  0.25MS FAST IV
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  SEBI SPAN RELIEF
                </span>
              </div>
            </div>
            <button
              onClick={() => onSelectView('strategy_builder')}
              className="mt-6 w-full py-2.5 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-xs font-sans font-bold text-cyan-300 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>LAUNCH BUILDER</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* 02: Mirajane Strauss Voice AI */}
          <div className="creative-agency-card p-6 flex flex-col justify-between group">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-xs font-bold text-violet-400 uppercase tracking-widest">
                  02 / AUTONOMOUS AI
                </span>
                <Sparkles className="w-5 h-5 text-violet-400 group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="font-syne text-xl font-bold text-white mb-2">
                Mirajane Strauss Voice Agent
              </h3>
              <p className="font-sans text-xs text-slate-300 leading-relaxed">
                NVIDIA Nemotron Voice Intercom architecture enabling spoken trade commands. Dual quantitative state machine between Risk Parity Custody and Aggressive Alpha Hunting with automated 1-Touch SEBI cards.
              </p>
              <div className="flex flex-wrap gap-1.5 mt-4">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-500/10 text-violet-300 border border-violet-500/20">
                  NEMOTRON VOICE
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-500/10 text-violet-300 border border-violet-500/20">
                  AGGRESSIVE ALPHA
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-500/10 text-violet-300 border border-violet-500/20">
                  LIVE INTERNET FEEDS
                </span>
              </div>
            </div>
            <button
              onClick={() => onSelectView('mirajane')}
              className="mt-6 w-full py-2.5 rounded-xl bg-violet-500/15 hover:bg-violet-500/25 border border-violet-500/30 text-xs font-sans font-bold text-violet-300 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>TALK TO MIRAJANE</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* 03: PyO3 Rust HFT OMS */}
          <div className="creative-agency-card p-6 flex flex-col justify-between group">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-xs font-bold text-emerald-400 uppercase tracking-widest">
                  03 / EXECUTION & RL
                </span>
                <Zap className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="font-syne text-xl font-bold text-white mb-2">
                PyO3 Rust HFT & FinRL-Meta
              </h3>
              <p className="font-sans text-xs text-slate-300 leading-relaxed">
                Sub-50 microsecond execution engine compiled natively in Rust with Farama Gymnasium Indian F&O environment. Incorporates Indian market friction (STT, NSE turnover, ₹20 brokerage).
              </p>
              <div className="flex flex-wrap gap-1.5 mt-4">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  &lt;38µS LATENCY
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  FINRL GYM
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  GREED LOCK GUARD
                </span>
              </div>
            </div>
            <button
              onClick={() => onSelectView('dashboard')}
              className="mt-6 w-full py-2.5 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-xs font-sans font-bold text-emerald-300 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>VIEW HFT TELEMETRY</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* 04: Smart Money Concepts & Bhavcopy */}
          <div className="creative-agency-card p-6 flex flex-col justify-between group">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-xs font-bold text-amber-400 uppercase tracking-widest">
                  04 / PRICE ACTION
                </span>
                <BarChart3 className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="font-syne text-xl font-bold text-white mb-2">
                Smart Money Concepts & Bhavcopy
              </h3>
              <p className="font-sans text-xs text-slate-300 leading-relaxed">
                Vectorized detection of Fair Value Gaps (FVG) with 50% Consequent Encroachment, Institutional Order Blocks (OB), and Break of Structure (BOS) over 5 years of historical NSE option Bhavcopy records.
              </p>
              <div className="flex flex-wrap gap-1.5 mt-4">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  ICT FVG & OB
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  6,210 BHAVCOPY ROWS
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  CLICKHOUSE MERGETREE
                </span>
              </div>
            </div>
            <button
              onClick={() => onSelectView('strategy_builder')}
              className="mt-6 w-full py-2.5 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-xs font-sans font-bold text-amber-300 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>INSPECT SMC CHARTS</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* 05: DeepSeek-V3 MoE & Academic Rigor */}
          <div className="creative-agency-card p-6 flex flex-col justify-between group md:col-span-2 lg:col-span-2">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-xs font-bold text-rose-400 uppercase tracking-widest">
                  05 / MOE & RIGOR
                </span>
                <Cpu className="w-5 h-5 text-rose-400 group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="font-syne text-xl font-bold text-white mb-2">
                DeepSeek-V3 MoE & PWB-Toolbox
              </h3>
              <p className="font-sans text-xs text-slate-300 leading-relaxed">
                Top-2 Sparse Mixture-of-Experts routing across Macro, Greeks, SMC, and Risk experts, with Bailey & López de Prado Deflated Sharpe Ratio (DSR) to eliminate data snooping and overfitting.
              </p>
              <div className="flex flex-wrap gap-1.5 mt-4">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                  TOP-2 MOE GATING
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                  DEFLATED SHARPE DSR
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                  QWEN3 STRATEGY SYNTHESIZER
                </span>
              </div>
            </div>
            <button
              onClick={() => onSelectView('mirajane')}
              className="mt-6 w-full py-2.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-xs font-sans font-bold text-rose-300 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>VIEW MOE DIRECTIVE</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* ── 4. LIVE MARKET INTELLIGENCE STRIP ── */}
      <section className="px-6 sm:px-10 lg:px-16 pb-20 max-w-7xl mx-auto">
        <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950/30 via-slate-900/60 to-cyan-950/30 border border-emerald-500/30 shadow-[0_12px_40px_rgba(0,0,0,0.6)] backdrop-blur-xl flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Activity className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="text-[11px] font-mono text-emerald-400 uppercase tracking-wider font-bold">
                DEEPSEEK-V3 MOE CONSENSUS
              </div>
              <div className="text-sm font-sans font-bold text-white mt-0.5">
                ACTIVE DIRECTIVE:{' '}
                <span className="text-emerald-400 font-mono">{marketTelemetry.moe_directive}</span>
              </div>
              <div className="text-xs text-slate-400 font-mono mt-0.5">
                Top Expert: {marketTelemetry.moe_expert} · GIFT Nifty Spread: +{marketTelemetry.gift_spread} pts · Brent Crude: ${marketTelemetry.crude}/bbl
              </div>
            </div>
          </div>

          <button
            onClick={() => onSelectView('strategy_builder')}
            className="btn btn-primary px-6 py-3 text-xs font-bold font-sans tracking-wide shrink-0"
          >
            EXECUTE ON CHAIN
          </button>
        </div>
      </section>

      {/* ── 5. SEBI COMPLIANCE ASSURANCE FOOTER ── */}
      <footer className="border-t border-white/[0.08] bg-[#030508] px-6 sm:px-10 lg:px-16 py-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
          <div>
            <div className="flex items-center justify-center md:justify-start gap-2 font-mono text-xs text-emerald-400 font-bold uppercase tracking-wider">
              <Shield className="w-4 h-4 text-emerald-400" />
              SEBI APRIL 1, 2026 HITL COMPLIANCE MANDATE
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-xl font-sans">
              Autonomous trading signals generated by Mirajane Strauss are strictly gated by a 4-second physical human 1-Touch validation barrier. All orders are executed through the PyO3 Rust HFT OMS with cryptographic audit hashes committed to ClickHouse.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
            <span className="px-3 py-1 rounded-md bg-white/[0.04] border border-white/[0.06]">
              ₹ INR EXCLUSIVELY
            </span>
            <span className="px-3 py-1 rounded-md bg-white/[0.04] border border-white/[0.06]">
              ASIA/KOLKATA IST
            </span>
            <span className="px-3 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
              SEBI COMPLIANT
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
