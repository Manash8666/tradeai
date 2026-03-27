import { motion } from 'framer-motion';
import { Lock, Target, TrendingUp, ShieldX } from 'lucide-react';
import { useState, useEffect } from 'react';

export function GreedCircuitBreaker() {
  const profitTarget = 50000; // Target in INR
  const maxLoss = -15000;
  
  const [currentPnL, setCurrentPnL] = useState(24500); // Simulated active P&L
  const [isLocked, setIsLocked] = useState(false);
  const [lockReason, setLockReason] = useState("");

  // Simulated algorithmic trading progress for presentation purposes
  useEffect(() => {
    if (isLocked) return;

    const interval = setInterval(() => {
        setCurrentPnL(prev => {
            const slip = prev + (Math.random() * 2000 - 500); // Bias upward
            if (slip >= profitTarget) {
                setIsLocked(true);
                setLockReason("PROFIT TARGET SECURED");
                return profitTarget;
            }
            if (slip <= maxLoss) {
                setIsLocked(true);
                setLockReason("MAX DRAWDOWN HIT");
                return maxLoss;
            }
            return slip;
        });
    }, 4000);

    return () => clearInterval(interval);
  }, [isLocked]);

  const pnlRatio = isLocked ? 100 : Math.max(0, (currentPnL / profitTarget) * 100);
  const isProfit = currentPnL >= 0;

  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`glass-panel p-6 border-l-4 overflow-hidden relative transition-all duration-700 ${
         isLocked 
         ? 'border-l-[var(--color-primary)] bg-[var(--color-primary-10)] shadow-[0_0_30px_rgba(0,255,136,0.1)]' 
         : 'border-l-indigo-500'
      }`}
    >
      <div className="relative z-10">
        
        <div className="flex justify-between items-center mb-6 w-full">
            <div className="flex items-center gap-3">
               <div className={`p-2 rounded ${isLocked ? 'bg-[var(--color-primary)]' : 'bg-indigo-500'}`}>
                  {isLocked ? <Lock size={20} className="text-black" /> : <Target size={20} className="text-white" />}
               </div>
               <div>
                  <h2 className={`text-lg font-black tracking-widest flex flex-col ${isLocked ? 'text-[var(--color-primary)]' : 'text-white'}`}>
                     PSYCHOLOGICAL GREED LOCK
                     <span className="text-[10px] text-gray-500 font-mono tracking-normal">BEHAVIORAL OVER-TRADING BREAKER</span>
                  </h2>
               </div>
            </div>

            <div className="text-right">
                <div className={`text-2xl font-mono font-black tracking-tighter ${isProfit ? 'text-emerald-400' : 'text-red-400'}`}>
                   {isProfit ? '+' : ''}₹{currentPnL.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </div>
                <div className="text-[10px] text-gray-500 font-mono mt-1">REALIZED P&L</div>
            </div>
        </div>

        {isLocked ? (
            <motion.div 
               initial={{ scale: 0.9, opacity: 0 }}
               animate={{ scale: 1, opacity: 1 }}
               className="bg-[#0b101e] border-2 border-[var(--color-primary)] p-4 rounded-lg flex items-center justify-between shadow-[inset_0_0_20px_rgba(0,255,136,0.1)] relative overflow-hidden"
            >
               <div className="absolute inset-0 bg-[var(--color-primary)] opacity-5 animate-pulse"></div>
               <div className="flex items-center gap-3 relative z-10">
                  <ShieldX size={32} className="text-[var(--color-primary)]" />
                  <div>
                     <div className="text-sm font-black text-white tracking-widest">{lockReason}</div>
                     <div className="text-[10px] text-[var(--color-primary)] font-mono uppercase">
                        Terminal Frozen until Midnight IST. Operations Secured.
                     </div>
                  </div>
               </div>
               <div className="text-3xl font-black text-white/5 opacity-50 select-none absolute right-[-20px] -rotate-12">
                   LOCKED
               </div>
            </motion.div>
        ) : (
            <div>
               <div className="flex justify-between text-[10px] font-mono mb-2 text-gray-400">
                  <span>₹0</span>
                  <span className="text-emerald-400 font-bold">TARGET: +₹{profitTarget.toLocaleString('en-IN')}</span>
               </div>
               <div className="h-2 bg-gray-900 rounded-full overflow-hidden border border-gray-800">
                   <motion.div 
                      className="h-full bg-indigo-500 relative"
                      initial={{ width: 0 }}
                      animate={{ width: `${pnlRatio}%` }}
                      transition={{ type: "spring", stiffness: 50 }}
                   >
                      <div className="absolute top-0 right-0 bottom-0 w-8 bg-gradient-to-r from-transparent to-white/30"></div>
                   </motion.div>
               </div>
               <div className="flex items-center gap-2 mt-3 text-[10px] text-gray-500 font-mono">
                  <TrendingUp size={12} className="text-indigo-400" />
                  Limits over-trading. Blocks all executions categorically upon reaching target parameters natively.
               </div>
            </div>
        )}
      </div>
    </motion.div>
  );
}
