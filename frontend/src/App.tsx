import { useState } from 'react';
import { ThemeProvider } from './store/ThemeContext';
import { Header, type ActivePlatformView } from './components/Header';
import { CreativeShowcase } from './components/CreativeShowcase';
import { LiveTradingDesk } from './pages/LiveTradingDesk';
import { Dashboard } from './pages/Dashboard';
import { OptionStrategyBuilder } from './components/OptionStrategyBuilder';
import { MirajaneBotPanel } from './components/MirajaneBotPanel';
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  const [currentView, setCurrentView] = useState<ActivePlatformView>('live_trading');

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-[#05070c] text-slate-100 flex flex-col font-sans selection:bg-emerald-500/30 selection:text-emerald-300">
        <Header currentView={currentView} onSelectView={setCurrentView} />

        <main className="flex-1 w-full bg-[#05070c]">
          {currentView === 'showcase' && (
            <ErrorBoundary fallbackTitle="Creative Showcase">
              <CreativeShowcase onSelectView={setCurrentView} />
            </ErrorBoundary>
          )}

          {currentView === 'live_trading' && (
            <ErrorBoundary fallbackTitle="Live Trading Desk">
              <LiveTradingDesk />
            </ErrorBoundary>
          )}

          {currentView === 'strategy_builder' && (
            <div className="max-w-[1520px] mx-auto p-4 sm:p-6 lg:p-8 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-white/[0.06]">
                <div>
                  <h1 className="font-syne text-2xl font-black text-white tracking-tight uppercase">
                    OPTIONS STRATEGY BUILDER
                  </h1>
                  <p className="text-xs font-mono text-slate-400 mt-0.5">
                    Real-Time Option Chain · 32 Ready-Made Topologies · Peter Jäckel Fast IV &lt;0.25ms · SEBI SPAN Margin
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    NSE DERIVATIVES
                  </span>
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-mono text-slate-300 bg-white/[0.04] border border-white/[0.08]">
                    ₹ INR PRICING
                  </span>
                </div>
              </div>

              <ErrorBoundary fallbackTitle="Option Strategy Builder Module">
                <OptionStrategyBuilder />
              </ErrorBoundary>
            </div>
          )}

          {currentView === 'mirajane' && (
            <div className="max-w-6xl mx-auto p-4 sm:p-6 lg:p-8 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-white/[0.06]">
                <div>
                  <h1 className="font-syne text-2xl font-black text-white tracking-tight uppercase flex items-center gap-2">
                    MIRAJANE STRAUSS <span className="text-violet-400 font-extrabold">// VOICE AI</span>
                  </h1>
                  <p className="text-xs font-mono text-slate-400 mt-0.5">
                    NVIDIA Nemotron Voice Intercom · Live Global Internet Scanner · DeepSeek-V3 MoE · SEBI 1-Touch
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-mono font-bold bg-violet-500/10 text-violet-400 border border-violet-500/20">
                    VOICE INTERCOM ACTIVE
                  </span>
                </div>
              </div>

              <ErrorBoundary fallbackTitle="Mirajane Autonomous Bot">
                <MirajaneBotPanel onSelectView={setCurrentView} />
              </ErrorBoundary>
            </div>
          )}

          {currentView === 'dashboard' && (
            <ErrorBoundary fallbackTitle="Command Terminal">
              <Dashboard />
            </ErrorBoundary>
          )}
        </main>
      </div>
    </ThemeProvider>
  );
}

export default App;
