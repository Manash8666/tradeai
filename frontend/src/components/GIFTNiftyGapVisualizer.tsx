import { motion } from 'framer-motion';
import { Globe, ArrowUpRight, ArrowDownRight, Crosshair } from 'lucide-react';
import { useState, useEffect } from 'react';

export function GIFTNiftyGapVisualizer() {
  const [gapPoints, setGapPoints] = useState(120.45);
  const [sustainProb, setSustainProb] = useState(82.4);
  const [direction, setDirection] = useState('GAP_UP');
  
  // Simulated Overnight Oracle Polling
  useEffect(() => {
    const interval = setInterval(() => {
        setGapPoints(prev => {
            const shift = prev + (Math.random() * 4 - 2);
            setDirection(shift > 0 ? 'GAP_UP' : 'GAP_DOWN');
            return shift;
        });
        setSustainProb(prev => Math.min(Math.max(prev + (Math.random() * 2 - 1), 60), 95));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const isUp = direction === 'GAP_UP';

  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`glass-panel p-6 border-l-4 overflow-hidden relative ${isUp ? 'border-l-emerald-500' : 'border-l-rose-500'}`}
    >
      {/* GIFT Nifty Geographic Radar Effects */}
      <div className={`absolute -top-10 -right-10 w-48 h-48 rounded-full blur-3xl opacity-20 ${isUp ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-xl font-black text-white flex items-center gap-3 tracking-tight">
              <Globe className={isUp ? 'text-emerald-400' : 'text-rose-400'} />
              FII / GIFT NIFTY ARBITRAGE
            </h2>
            <p className="text-xs text-[var(--color-primary)] font-mono mt-1">
              9:07:59 AM IST Call Auction Equilibrium Sniper
            </p>
          </div>
          <div className="flex flex-col items-end">
             <span className="text-[10px] text-gray-500 uppercase tracking-widest bg-gray-900/50 px-2 py-1 rounded border border-gray-800 flex items-center gap-2">
                <Crosshair size={12} className="text-[var(--color-primary)] animate-pulse" />
                OVERNIGHT ORACLE ALIGNED
             </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="bg-[#0b101e] border border-[var(--color-primary-20)] p-4 rounded text-center relative">
            <div className="text-[10px] text-gray-500 tracking-wider mb-2">PREDICTED GAP</div>
            <div className={`text-3xl font-mono font-bold flex items-center justify-center gap-2 ${isUp ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isUp ? <ArrowUpRight size={24} /> : <ArrowDownRight size={24} />}
              {Math.abs(gapPoints).toFixed(2)}
            </div>
          </div>
          
          <div className="bg-[#0b101e] border border-[var(--color-primary-20)] p-4 rounded text-center relative overflow-hidden">
             <div 
               className="absolute bottom-0 left-0 h-1 bg-yellow-500 transition-all duration-1000" 
               style={{ width: `${sustainProb}%` }}
             ></div>
            <div className="text-[10px] text-gray-500 tracking-wider mb-2">SUSTAIN PROBABILITY</div>
            <div className="text-2xl font-mono text-yellow-500 font-bold">{sustainProb.toFixed(1)}%</div>
          </div>

          <div className="bg-[#0b101e] border border-[var(--color-primary-20)] p-4 rounded text-center relative flex flex-col justify-center">
             <div className="text-[10px] text-gray-500 tracking-wider mb-1">EXECUTION WINDOW</div>
             <div className="text-lg font-mono text-white font-bold tracking-widest border border-gray-800 bg-gray-900 mx-2 py-1 rounded shadow-inner">09:07:59</div>
             <div className="text-[9px] text-gray-600 mt-1">IST (UTC+5:30)</div>
          </div>
        </div>

        <div className="flex gap-4">
            <div className="flex-1 text-[10px] text-gray-400 font-mono bg-[#0b101e] p-2 rounded border border-gray-800/50">
               <span className="text-[var(--color-primary)] block mb-1">FII Net Index F&O: +12,500</span>
               Institutional volume synthetically compressing Asian offshore premiums.
            </div>
            <div className="flex-1 text-[10px] text-gray-400 font-mono bg-[#0b101e] p-2 rounded border border-gray-800/50">
               <span className="text-[var(--color-primary)] block mb-1">Global S&P500 Vector: +0.8%</span>
               Overnight geographic thrust confirmed overriding localized standard deviation.
            </div>
        </div>
      </div>
    </motion.div>
  );
}
