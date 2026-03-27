import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, ShieldCheck, Zap } from 'lucide-react';

interface Alert {
  id: string;
  timestamp: string;
  symbol: string;
  type: 'spoofing' | 'layering' | 'latency_spike';
  risk_score: number;
  explanation: string;
}

export function ManipulationAlertsList() {
  // Mock Data generating RTMD-AI SHAP Explanations locally
  const activeAlerts: Alert[] = [
    {
      id: 'a1b2',
      timestamp: new Date().toLocaleTimeString(),
      symbol: 'NIFTY',
      type: 'spoofing',
      risk_score: 94,
      explanation: 'Flagged primarily due to anomalous orderbook_imbalance deviating +4σ globally.'
    },
    {
      id: 'c3d4',
      timestamp: new Date(Date.now() - 45000).toLocaleTimeString(),
      symbol: 'SBIN',
      type: 'latency_spike',
      risk_score: 68,
      explanation: 'Warning: Artificial tick latency injection mapped crossing 90ms bounds.'
    }
  ];

  return (
    <div className="glass-panel p-6 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-6">
        <ShieldCheck className="text-gold-400" size={24} />
        <h2 className="text-xl font-bold bg-gradient-to-r from-gold-100 to-gold-300 bg-clip-text text-transparent">
          SEBI Watch: XAI Defense
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        <AnimatePresence>
          {activeAlerts.map((alert) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`p-4 rounded-lg border flex flex-col gap-2 relative overflow-hidden ${
                alert.risk_score > 85 
                  ? 'bg-red-900/10 border-red-500/30' 
                  : 'bg-orange-900/10 border-orange-500/30'
              }`}
            >
              <div className="flex justify-between items-center text-sm font-mono">
                <span className="text-ocean-100 font-bold">{alert.symbol}</span>
                <span className="text-ocean-300/70">{alert.timestamp}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className={alert.risk_score > 85 ? 'text-red-400' : 'text-orange-400'} />
                <span className="font-semibold text-white/90 uppercase text-sm tracking-wide">
                  {alert.type.replace('_', ' ')}
                </span>
                <span className={`text-xs ml-auto font-mono px-2 py-0.5 rounded ${
                  alert.risk_score > 85 ? 'bg-red-500/20 text-red-200' : 'bg-orange-500/20 text-orange-200'
                }`}>
                  RISK: {alert.risk_score}
                </span>
              </div>
              
              <div className="mt-2 text-xs text-ocean-200/80 leading-relaxed font-mono bg-black/20 p-2 rounded relative">
                <span className="absolute -top-2 -left-1 bg-ocean-800 text-[9px] px-1 text-white border border-ocean-600 rounded">SHAP</span>
                {alert.explanation}
              </div>
              
              <div className="mt-3 flex gap-2">
                <button className="flex-1 py-1.5 text-xs font-bold text-white bg-red-500/20 hover:bg-red-500/40 border border-red-500/30 rounded transition-colors flex items-center justify-center gap-1">
                  <Zap size={14} /> LIQUIDATE ALL
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
