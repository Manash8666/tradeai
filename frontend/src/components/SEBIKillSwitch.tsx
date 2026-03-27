import { motion } from 'framer-motion';
import { AlertTriangle, PowerOff, ShieldCheck, FileKey } from 'lucide-react';
import { useState } from 'react';

export function SEBIKillSwitch() {
  const [isKilled, setIsKilled] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const executeKillSwitch = () => {
      setIsKilled(true);
      setConfirming(false);
      // Native API call to backend would fire here triggering `sebi_ptrc_killswitch.py`
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`glass-panel p-4 border border-x-0 sm:border-x sm:rounded-lg overflow-hidden relative transition-all duration-500 ${
         isKilled 
         ? 'bg-red-500/10 border-red-500/50 shadow-[0_0_50px_rgba(239,68,68,0.3)]' 
         : 'bg-zinc-900/50 border-gray-800'
      }`}
    >
      <div className="flex justify-between items-center sm:items-start flex-col sm:flex-row gap-4">
        
        <div className="flex items-start gap-4 flex-1">
          <div className={`p-3 rounded-full ${isKilled ? 'bg-red-500' : 'bg-zinc-800'}`}>
             {isKilled ? <PowerOff size={28} className="text-white animate-pulse" /> : <ShieldCheck size={28} className="text-emerald-500" />}
          </div>
          
          <div>
             <h2 className="text-xl font-black text-white tracking-widest flex items-center gap-2">
                SEBI MASTER KILL SWITCH
                {isKilled && <span className="bg-red-500 text-xs px-2 py-0.5 rounded text-white animate-pulse">ENGAGED</span>}
             </h2>
             <div className="text-xs text-gray-400 font-mono mt-1 w-full max-w-md">
                 Federally mandated emergency OMS severance. Triggers absolute cancellation of pending routes, flattening of unhedged matrices natively, and severs Python/Rust bridging instantaneously. 
             </div>
             
             {!isKilled && (
                 <div className="flex gap-4 mt-3">
                    <div className="flex items-center gap-1.5 text-[10px] text-gray-500 font-mono">
                       <ShieldCheck size={12} className="text-emerald-500" /> PTRC Guard Active
                    </div>
                    <div className="flex items-center gap-1.5 text-[10px] text-gray-500 font-mono">
                       <FileKey size={12} className="text-[var(--color-primary)]" /> 5-Year SHA-256 Ledger
                    </div>
                 </div>
             )}
          </div>
        </div>

        <div>
            {!isKilled ? (
                confirming ? (
                    <div className="flex items-center gap-2 bg-red-950/50 p-2 rounded border border-red-900/50">
                        <button 
                           onClick={() => setConfirming(false)}
                           className="px-4 py-2 text-xs font-bold text-gray-400 hover:text-white transition-colors"
                        >
                           CANCEL
                        </button>
                        <button 
                           onClick={executeKillSwitch}
                           className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white font-black tracking-widest rounded transition-colors shadow-[0_0_15px_rgba(220,38,38,0.6)] animate-pulse flex items-center gap-2"
                        >
                           <AlertTriangle size={16} />
                           CONFIRM HALT
                        </button>
                    </div>
                ) : (
                    <button 
                       onClick={() => setConfirming(true)}
                       className="px-8 py-4 bg-zinc-800 hover:bg-red-900 border border-zinc-700 hover:border-red-700 text-red-500 hover:text-red-400 font-black tracking-widest rounded-lg transition-all duration-300 w-full sm:w-auto"
                    >
                       DISABLE ALGORITHMS
                    </button>
                )
            ) : (
                <div className="px-8 py-4 bg-red-950 border border-red-900 text-red-500 font-black tracking-widest rounded-lg text-center font-mono">
                   SYSTEM HALTED NATIVELY
                </div>
            )}
        </div>
      </div>
    </motion.div>
  );
}
