import { useState } from 'react';
import { motion } from 'framer-motion';
import { BrainCircuit, MessageSquareText, TrendingDown, TrendingUp } from 'lucide-react';

export function NLP_Agent_Feed() {
  const [events] = useState([
    { id: 1, text: "SEBI investigates flash-crash anomalies in mid-cap IT sector.", sentiment: "Negative", score: 0.94 },
    { id: 2, text: "Reliance Q3 Earnings surpass street estimates driven by Jio.", sentiment: "Positive", score: 0.88 },
    { id: 3, text: "RBI holds repo rate steady; Banking sector neutral.", sentiment: "Neutral", score: 0.65 },
  ]);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-6 h-full border-[var(--color-primary-20)]"
    >
      <div className="flex items-center justify-between border-b border-[var(--color-primary-20)] pb-4 mb-4">
        <h2 className="text-xl font-bold flex items-center gap-3 text-white">
          <BrainCircuit className="text-[var(--color-primary)]" />
          Autonomous Swarm & FinBERT NLP
        </h2>
        <div className="flex items-center gap-2">
           <span className="relative flex h-3 w-3">
             <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-primary)] opacity-75"></span>
             <span className="relative inline-flex rounded-full h-3 w-3 bg-[var(--color-primary)]"></span>
           </span>
           <span className="text-xs font-mono text-[var(--color-primary)]">AGENTS ACTIVE</span>
        </div>
      </div>

      <div className="space-y-4">
        {events.map((ev) => (
          <div key={ev.id} className="relative p-4 bg-[var(--color-bg-tertiary)] rounded-lg border border-[var(--color-primary-10)] overflow-hidden group">
            {/* Ambient Base Styling */}
             <div className="absolute inset-0 bg-gradient-to-r from-[var(--color-bg-primary)] to-transparent opacity-0 group-hover:opacity-10 transition-opacity"></div>
             
             <div className="flex justify-between items-start mb-2">
                 <div className="flex items-center gap-2">
                     <MessageSquareText size={14} className="text-[var(--color-text-muted)]" />
                     <span className="text-xs font-mono text-[var(--color-text-muted)] tracking-wider">EVENT STREAM {ev.id}</span>
                 </div>
                 <div className="flex items-center gap-1">
                     {ev.sentiment === "Positive" ? <TrendingUp size={14} className="text-green-400" /> : <TrendingDown size={14} className="text-red-400" />}
                     <span className={`text-xs font-bold font-mono ${ev.sentiment === "Positive" ? "text-green-400" : ev.sentiment === "Negative" ? "text-red-400" : "text-gray-400"}`}>
                        {(ev.score * 100).toFixed(1)}% {ev.sentiment.toUpperCase()}
                     </span>
                 </div>
             </div>
             <p className="text-sm text-[var(--color-text-primary)] font-medium leading-relaxed">
                 "{ev.text}"
             </p>
             <div className="mt-3 flex gap-2">
                <span className="text-[10px] bg-[var(--color-bg-primary)] border border-[var(--color-primary-20)] px-2 py-1 rounded text-[var(--color-primary)] font-mono">FINBERT_ENCODED</span>
                <span className="text-[10px] bg-[var(--color-bg-primary)] border border-[var(--color-primary-20)] px-2 py-1 rounded text-[var(--color-primary)] font-mono">SWARM_VERIFIED</span>
             </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
