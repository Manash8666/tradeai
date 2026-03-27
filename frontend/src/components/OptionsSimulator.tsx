import { useState } from 'react';
import { motion } from 'framer-motion';
import { Binary } from 'lucide-react';

export function OptionsSimulator() {
  const [strike, setStrike] = useState(22500);
  const [spot] = useState(22450);
  const [volatility, setVolatility] = useState(14.5);
  const [days, setDays] = useState(3);

  // Proprietary localized math simulating the backend `derivatives.py` payload
  const d1 = (Math.log(spot / strike) + (0.07 + 0.5 * Math.pow(volatility / 100, 2)) * (days / 365)) / ((volatility / 100) * Math.sqrt(days / 365));
  
  // N(x) approximation for UI
  const cdf = (x: number) => {
      const t = 1 / (1 + 0.2316419 * Math.abs(x));
      const d = 0.3989423 * Math.exp(-x * x / 2);
      const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
      return x > 0 ? 1 - p : p;
  };
  
  const callDelta = cdf(d1);
  const putDelta = callDelta - 1;

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-panel p-6"
    >
      <div className="flex items-center justify-between border-b border-[var(--color-primary-20)] pb-4 mb-6">
        <h2 className="text-xl font-bold flex items-center gap-3 text-white">
          <Binary className="text-[var(--color-primary)]" />
          Proprietary Greek Simulator
        </h2>
        <span className="text-xs font-mono px-2 py-1 bg-[var(--color-primary-20)] text-[var(--color-primary)] rounded">
          Algorithmic Pricing Core
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
         <div className="p-4 rounded-lg bg-[var(--color-bg-tertiary)] border border-[var(--color-primary-10)]">
             <label className="text-xs text-[var(--color-text-muted)] font-mono block mb-2">TARGET STRIKE</label>
             <input type="range" min={21000} max={24000} step={50} value={strike} onChange={(e) => setStrike(Number(e.target.value))} className="w-full market-cap-slider" />
             <div className="text-right text-lg font-mono text-[var(--color-text-primary)] mt-2">₹{strike}</div>
         </div>
         <div className="p-4 rounded-lg bg-[var(--color-bg-tertiary)] border border-[var(--color-primary-10)]">
             <label className="text-xs text-[var(--color-text-muted)] font-mono block mb-2">IMPLIED VOL (IV)</label>
             <input type="range" min={8} max={40} step={0.5} value={volatility} onChange={(e) => setVolatility(Number(e.target.value))} className="w-full market-cap-slider" />
             <div className="text-right text-lg font-mono text-[var(--color-text-primary)] mt-2">{volatility}%</div>
         </div>
         <div className="p-4 rounded-lg bg-[var(--color-bg-tertiary)] border border-[var(--color-primary-10)]">
             <label className="text-xs text-[var(--color-text-muted)] font-mono block mb-2">DAYS TO EXPIRY</label>
             <input type="range" min={0.5} max={30} step={0.5} value={days} onChange={(e) => setDays(Number(e.target.value))} className="w-full market-cap-slider" />
             <div className="text-right text-lg font-mono text-[var(--color-text-primary)] mt-2">{days}DTE</div>
         </div>
         <div className="p-4 rounded-lg bg-[var(--color-bg-tertiary)] border border-[var(--color-primary-10)] flex flex-col justify-center items-center">
             <label className="text-xs text-[var(--color-text-muted)] font-mono block mb-2">SPAN MARGIN (SELL)</label>
             <div className="text-2xl font-black text-[var(--color-primary)]">
                ₹{((spot * 50 * 0.11) * (strike > spot ? 0.6 : 1)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
             </div>
         </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
         <div className="p-4 bg-[var(--color-bg-primary)] rounded border border-[var(--color-primary-20)] relative overflow-hidden">
            <div className="scanline" />
            <div className="text-xs text-[var(--color-text-muted)] font-mono mb-1">CALL (CE) DELTA</div>
            <div className="text-3xl font-mono text-green-400">{callDelta.toFixed(4)}</div>
         </div>
         <div className="p-4 bg-[var(--color-bg-primary)] rounded border border-[var(--color-primary-20)] relative overflow-hidden">
            <div className="scanline" />
            <div className="text-xs text-[var(--color-text-muted)] font-mono mb-1">PUT (PE) DELTA</div>
            <div className="text-3xl font-mono text-red-400">{putDelta.toFixed(4)}</div>
         </div>
      </div>
    </motion.div>
  );
}
