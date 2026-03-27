import { useState } from 'react';
import { motion } from 'framer-motion';
import { Target, Zap, ShieldCheck } from 'lucide-react';

export function IndianExpiryMatrix() {
  const [currentDay] = useState(new Date().getDay() - 1); // 0 = Mon, 4 = Fri
  // Fallback to Monday if it's the weekend
  const safeDay = currentDay < 0 || currentDay > 4 ? 0 : currentDay;

  const [expiryData] = useState([
    { day: 'Monday', index: 'Midcap Nifty / Bankex', symbol: 'MIDCPNIFTY / BANKEX', isToday: false, volatility: 14.2, status: 'STANDBY', exchange: 'NSE/BSE' },
    { day: 'Tuesday', index: 'Financial Nifty', symbol: 'FINNIFTY', isToday: false, volatility: 16.5, status: 'STANDBY', exchange: 'NSE' },
    { day: 'Wednesday', index: 'Bank Nifty', symbol: 'BANKNIFTY', isToday: false, volatility: 18.9, status: 'STANDBY', exchange: 'NSE' },
    { day: 'Thursday', index: 'Nifty 50', symbol: 'NIFTY', isToday: false, volatility: 13.5, status: 'STANDBY', exchange: 'NSE' },
    { day: 'Friday', index: 'Sensex', symbol: 'SENSEX', isToday: false, volatility: 15.1, status: 'STANDBY', exchange: 'BSE' }
  ]);

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-panel p-6 border-l-4 border-l-red-500 overflow-hidden relative"
    >
      {/* Background Warning Mesh */}
      <div className="absolute inset-0 bg-[url('/noise.svg')] opacity-5 mix-blend-overlay"></div>
      <div className="absolute -right-20 -top-20 w-64 h-64 bg-red-500/10 rounded-full blur-3xl"></div>

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-6 border-b border-[var(--color-primary-20)] pb-4">
            <div>
              <h2 className="text-2xl font-black text-white flex items-center gap-3 tracking-tighter">
                <Target className="text-red-500" />
                NSE 0DTE HUNTING MATRIX
              </h2>
              <p className="text-xs text-[var(--color-text-muted)] font-mono mt-1 w-3/4">
                Algorithm dynamically shifts global execution liquidity strictly to today's 0DTE index to exploit intra-day Gamma spikes and extreme Retail IV crush.
              </p>
            </div>
            <div className="text-right">
                <span className="flex items-center justify-end gap-2 text-xs font-mono text-red-400 mb-1">
                    <ShieldCheck size={14} /> PEAK MARGIN DEFENSE
                </span>
                <span className="text-xs font-mono text-yellow-500 bg-yellow-500/10 px-2 py-1 rounded">ICEBERG SLICING ACTIVE</span>
            </div>
        </div>

        <div className="grid grid-cols-5 gap-2 mb-6">
            {expiryData.map((item, idx) => {
                const isActive = idx === safeDay;
                return (
                    <div 
                        key={idx} 
                        className={`flex flex-col items-center justify-between p-3 rounded-lg border transition-all duration-500 ${
                            isActive 
                            ? 'bg-red-500/20 border-red-500 scale-105 shadow-[0_0_20px_rgba(239,68,68,0.3)]' 
                            : 'bg-[var(--color-bg-tertiary)] border-[var(--color-primary-10)] opacity-50'
                        }`}
                    >
                        <div className="text-center">
                            <span className={`text-[10px] font-black ${isActive ? 'text-white' : 'text-gray-500'}`}>{item.day.toUpperCase().substring(0, 3)}</span>
                            <span className={`text-sm font-bold tracking-tight mt-1 block ${isActive ? 'text-red-400' : 'text-gray-400'}`}>{item.index}</span>
                        </div>
                        {isActive && (
                            <motion.div 
                                initial={{ opacity: 0, y: 5 }} 
                                animate={{ opacity: 1, y: 0 }} 
                                className="mt-2 text-center"
                            >
                                <span className="text-[10px] bg-red-500 text-white px-2 py-1 rounded font-bold animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.5)]">
                                    ACTIVE 0DTE TARGET
                                </span>
                            </motion.div>
                        )}
                        
                        <div className="flex justify-between items-end mt-2 w-full">
                            <div>
                               <div className="text-[10px] text-gray-500 font-mono tracking-widest">{item.exchange} L2 HEATMAP</div>
                               <div className="text-xl font-bold font-mono tracking-tighter text-[var(--color-primary)]">
                                 {item.symbol}
                               </div>
                            </div>
                        </div>
                    </div>
                )
            })}
        </div>

        <div className="bg-[#0b101e] border border-red-500/30 rounded p-4 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-red-500"></div>
            <div className="flex justify-between items-center">
                <div>
                   <h3 className="text-white font-bold text-sm mb-1 flex items-center gap-2">
                      <Zap size={16} className="text-red-500" />
                      Dynamic Order Formatting (SEBI Limits)
                   </h3>
                   <p className="text-xs text-gray-400 font-mono">Breaking 50,000 QTY limits identically across 30 nano-slices.</p>
                </div>
                <div className="text-right">
                    <div className="text-3xl font-mono font-black text-red-500">14.2ms</div>
                    <div className="text-[10px] text-gray-400 font-mono">AVG EXECUTION LATENCY</div>
                </div>
            </div>
        </div>
      </div>
    </motion.div>
  );
}
