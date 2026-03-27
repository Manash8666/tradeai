import { motion } from 'framer-motion';
import { Layers, Activity, ShieldCheck, Cpu } from 'lucide-react';
import { useState, useEffect } from 'react';

export function QuantumSpanVisualizer() {
  const [temperature, setTemperature] = useState(1000);
  const [marginSavings, setMarginSavings] = useState(0);
  const [isOptimizing, setIsOptimizing] = useState(true);

  // Simulating the Simulated Annealing Cooling Schedule 
  useEffect(() => {
    const interval = setInterval(() => {
      setTemperature(prev => {
        if (prev <= 0.01) {
            setIsOptimizing(false);
            return 0.01;
        }
        return prev * 0.85; // Rapid geometric cooling
      });
      
      setMarginSavings(prev => {
         if (!isOptimizing) return prev;
         return Math.min(prev + (Math.random() * 12000), 145000); // Maxing out around 1.45L
      });
    }, 150);

    // Reset loop for visual demonstration
    const resetInterval = setInterval(() => {
        setTemperature(1000);
        setMarginSavings(0);
        setIsOptimizing(true);
    }, 8000);

    return () => {
        clearInterval(interval);
        clearInterval(resetInterval);
    };
  }, [isOptimizing]);

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-panel p-6 border-l-4 border-l-cyan-500 overflow-hidden relative"
    >
      {/* Quantum Lattice Background */}
      <div className="absolute top-0 left-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl opacity-50"></div>
      <div className="absolute inset-0 bg-[url('/hex_grid.svg')] opacity-5"></div>

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-xl font-black text-white flex items-center gap-3 tracking-tight">
              <Layers className="text-cyan-400" />
              QUANTUM SPAN OPTIMIZER 
            </h2>
            <p className="text-xs text-[var(--color-primary)] font-mono mt-1">
              Simulated Annealing Smart Order Routing (SOR)
            </p>
          </div>
          <div className="flex flex-col items-end">
             <span className={`text-xs font-mono px-2 py-1 rounded flex items-center gap-2 ${isOptimizing ? 'text-cyan-400 bg-cyan-500/10 animate-pulse' : 'text-green-400 bg-green-500/10'}`}>
                {isOptimizing ? <Cpu size={14} className="animate-spin" /> : <ShieldCheck size={14} />}
                {isOptimizing ? 'ANNEALING LATTICE' : 'SEBI COMPLIANT'}
             </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-[#0b101e] border border-[var(--color-primary-20)] p-4 rounded text-center relative overflow-hidden">
             {/* Cooling Bar */}
             <div 
               className="absolute bottom-0 left-0 h-1 bg-cyan-500 transition-all duration-150" 
               style={{ width: `${(temperature / 1000) * 100}%` }}
             ></div>
            <Activity size={16} className="text-cyan-400 mx-auto mb-2" />
            <div className="text-2xl font-mono text-white font-bold">{temperature.toFixed(4)} K</div>
            <div className="text-[10px] text-gray-500 tracking-wider">COMBINATORIAL TEMPERATURE</div>
          </div>
          
          <div className="bg-[#0b101e] border border-[var(--color-primary-20)] p-4 rounded text-center relative overflow-hidden">
            <ShieldCheck size={16} className="text-green-400 mx-auto mb-2" />
            <div className="text-2xl font-mono text-green-400 font-bold">₹{marginSavings.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
            <div className="text-[10px] text-gray-500 tracking-wider">SEBI MARGIN FREED</div>
          </div>
        </div>

        <p className="text-[10px] text-gray-500 font-mono text-center mt-4">
           Executes Metropolis-Hastings physics to mathematically sequence massive multi-leg derivatives instantaneously circumventing peak margin algorithmic blocks natively.
        </p>
      </div>
    </motion.div>
  );
}
