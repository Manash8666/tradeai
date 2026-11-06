import { motion } from 'framer-motion';
import {
  Zap,
  Sliders,
  Sparkles,
  Compass,
  Terminal,
  ShieldCheck,
  TrendingUp,
  Sun,
  Moon,
} from 'lucide-react';
import { useTheme } from '../store/ThemeContext';

export type ActivePlatformView = 'showcase' | 'live_trading' | 'strategy_builder' | 'mirajane' | 'dashboard';

interface HeaderProps {
  currentView?: ActivePlatformView;
  onSelectView?: (view: ActivePlatformView) => void;
}

export function Header({ currentView = 'showcase', onSelectView }: HeaderProps) {
  const { toggleTheme, isDark } = useTheme();

  const navItems = [
    {
      id: 'showcase' as const,
      label: 'Showcase Hub',
      icon: Compass,
      accent: 'emerald',
    },
    {
      id: 'live_trading' as const,
      label: 'Live Trading Desk',
      badge: 'LIVE CHARTS',
      icon: TrendingUp,
      accent: 'emerald',
    },
    {
      id: 'strategy_builder' as const,
      label: 'Strategy Builder',
      count: '32',
      icon: Sliders,
      accent: 'cyan',
    },
    {
      id: 'mirajane' as const,
      label: 'Mirajane Voice AI',
      icon: Sparkles,
      accent: 'violet',
    },
    {
      id: 'dashboard' as const,
      label: 'Command Terminal',
      icon: Terminal,
      accent: 'emerald',
    },
  ];

  return (
    <motion.header
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="sticky top-0 z-50 h-16 w-full px-6 flex items-center justify-between border-b border-white/[0.07] bg-[#05070c]/85 backdrop-blur-2xl"
    >
      {/* ── LEFT: Brand & Regulatory Seal ── */}
      <div
        onClick={() => onSelectView?.('showcase')}
        className="flex items-center gap-3.5 cursor-pointer group"
      >
        <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-500 p-[1px] shadow-[0_0_20px_rgba(0,255,136,0.25)] group-hover:shadow-[0_0_28px_rgba(0,255,136,0.45)] transition-all duration-300">
          <div className="w-full h-full rounded-[11px] bg-[#070b12] flex items-center justify-center">
            <Zap className="w-4 h-4 text-emerald-400 fill-emerald-400/20 group-hover:scale-110 transition-transform duration-300" />
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-syne text-[15px] font-black tracking-tight text-white flex items-center gap-1.5">
              ANTIGRAVITY <span className="text-emerald-400 font-extrabold">// QUANT</span>
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
              <ShieldCheck className="w-2.5 h-2.5" />
              SEBI 2026 HITL
            </span>
          </div>
          <p className="text-[10px] font-mono tracking-widest text-slate-400 uppercase">
            NSE · BSE · MCX · Direct Order Management System
          </p>
        </div>
      </div>

      {/* ── CENTER: 4 Sleek Navigation Pills ── */}
      {onSelectView && (
        <nav className="flex items-center p-1 rounded-xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectView(item.id)}
                className={`relative px-4 py-1.5 rounded-lg text-xs font-sans font-semibold tracking-wide flex items-center gap-2 transition-all duration-200 cursor-pointer ${
                  isActive
                    ? 'text-white bg-white/[0.10] shadow-[0_2px_12px_rgba(0,0,0,0.5)] border border-white/[0.12]'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                <Icon
                  className={`w-3.5 h-3.5 transition-colors ${
                    isActive
                      ? item.accent === 'emerald'
                        ? 'text-emerald-400'
                        : item.accent === 'cyan'
                        ? 'text-cyan-400'
                        : 'text-violet-400'
                      : 'text-slate-400'
                  }`}
                />
                <span>{item.label}</span>
                {item.count && (
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.2 rounded-full ${
                      isActive
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-bold'
                        : 'bg-white/[0.06] text-slate-400'
                    }`}
                  >
                    {item.count}
                  </span>
                )}
                {item.badge && (
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.2 rounded-full ${
                      isActive
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold'
                        : 'bg-white/[0.06] text-slate-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
                {isActive && (
                  <motion.div
                    layoutId="activeTabGlow"
                    className="absolute -bottom-1 left-3 right-3 h-[2px] bg-gradient-to-r from-emerald-400 via-cyan-400 to-violet-400 rounded-full"
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
              </button>
            );
          })}
        </nav>
      )}

      {/* ── RIGHT: Real-time Telemetry & Theme Toggle ── */}
      <div className="flex items-center gap-3">
        {/* Direct Market Access / OMS Status */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] font-mono font-bold text-emerald-400 tracking-wider">
            DIRECT OMS · NSE/BSE
          </span>
        </div>

        {/* Currency & Desk Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[11px] font-mono text-slate-300">
          <span className="text-emerald-400 font-bold">₹</span>
          <span>INR</span>
          <span className="text-slate-400">·</span>
          <span className="text-slate-400 text-[10px]">IST</span>
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="w-8 h-8 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] flex items-center justify-center text-slate-400 hover:text-white transition-all cursor-pointer"
        >
          {isDark ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-cyan-400" />}
        </button>
      </div>
    </motion.header>
  );
}
