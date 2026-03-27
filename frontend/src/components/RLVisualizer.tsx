import { motion } from 'framer-motion';
import { BrainCircuit, Activity, Cpu, Target } from 'lucide-react';
import { useState, useEffect } from 'react';

export function RLVisualizer() {
  const [epoch, setEpoch] = useState(1);
  const [reward, setReward] = useState(0);
  const [winRate, setWinRate] = useState(50.0);

  // Simulating the PPO Live Training metrics pumping from the PyTorch backend
  useEffect(() => {
    const interval = setInterval(() => {
      setEpoch(prev => prev + 1);
      setReward(prev => prev + (Math.random() * 20 - 5));
      setWinRate(prev => Math.min(Math.max(prev + (Math.random() * 2 - 0.8), 45), 85));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-6 border-l-4 border-l-purple-500 overflow-hidden relative"
    >
      {/* PPO Neural Background Effects */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl opacity-50"></div>
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-xl font-black text-white flex items-center gap-3 tracking-tight">
              <BrainCircuit className="text-purple-400" />
              PROXIMAL POLICY AI (PPO) 
            </h2>
            <p className="text-xs text-[var(--color-primary)] font-mono mt-1">
              Autonomous Reinforcement Learning Epoch Generation
            </p>
          </div>
          <div className="flex flex-col items-end">
             <span className="text-xs font-mono text-purple-400 bg-purple-500/10 px-2 py-1 rounded animate-pulse">SELF-TRAINING ACTIVE</span>
             <span className="text-[10px] text-gray-500 mt-1">Gym: NseOptionEnv-v1</span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="bg-[#0b101e] border border-[var(--color-primary-20)] p-4 rounded text-center">
            <Cpu size={16} className="text-gray-400 mx-auto mb-2" />
            <div className="text-2xl font-mono text-white font-bold">{epoch.toLocaleString()}</div>
            <div className="text-[10px] text-gray-500 tracking-wider">TRAINING EPOCHS</div>
          </div>
          
          <div className="bg-[#0b101e] border border-[var(--color-primary-20)] p-4 rounded text-center">
            <Activity size={16} className="text-green-400 mx-auto mb-2" />
            <div className="text-2xl font-mono text-green-400 font-bold">{winRate.toFixed(2)}%</div>
            <div className="text-[10px] text-gray-500 tracking-wider">ASYMPTOTIC SHARPE</div>
          </div>

          <div className="bg-[#0b101e] border border-[var(--color-primary-20)] p-4 rounded text-center">
            <Target size={16} className="text-purple-400 mx-auto mb-2" />
            <div className="text-2xl font-mono text-purple-400 font-bold">₹{reward.toFixed(0)}</div>
            <div className="text-[10px] text-gray-500 tracking-wider">CUMULATIVE REWARD</div>
          </div>
        </div>

        {/* Neural Network Visualization Graph Concept */}
        <div className="h-2 w-full bg-gray-900 rounded-full overflow-hidden flex gap-0.5">
           {[...Array(20)].map((_, i) => (
             <motion.div 
                key={i}
                initial={{ opacity: 0.3 }}
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1 }}
                className={`h-full flex-1 ${i % 3 === 0 ? 'bg-purple-500' : 'bg-[var(--color-primary)]'}`}
             />
           ))}
        </div>
        <div className="flex justify-between mt-2 px-1">
           <span className="text-[9px] text-gray-600 font-mono">STATE TENSOR (L2 Depth)</span>
           <span className="text-[9px] text-gray-600 font-mono">ACTION TENSOR (Buy/Sell/Hold)</span>
        </div>
      </div>
    </motion.div>
  );
}
