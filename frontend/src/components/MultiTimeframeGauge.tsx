import { motion } from 'framer-motion';

export function MultiTimeframeGauge() {
  const timeframes = [
    { label: '1m', signal: 'STRONG BUY', score: 92, direction: 'up' },
    { label: '5m', signal: 'BUY', score: 75, direction: 'up' },
    { label: '15m', signal: 'NEUTRAL', score: 50, direction: 'flat' },
    { label: '1H', signal: 'SELL', score: 35, direction: 'down' },
    { label: '1D', signal: 'STRONG SELL', score: 10, direction: 'down' }
  ];

  return (
    <div className="glass-panel p-6 h-full flex flex-col">
      <h2 className="text-xl font-bold bg-gradient-to-r from-ocean-100 to-ocean-300 bg-clip-text text-transparent mb-6">
        Multi-Timeframe Harmony
      </h2>
      
      <div className="flex-1 flex flex-col justify-around">
        {timeframes.map((tf, i) => (
          <motion.div 
            key={tf.label}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center gap-4 relative"
          >
            <div className="w-10 font-mono font-bold text-ocean-300">{tf.label}</div>
            
            <div className="flex-1 relative h-2 bg-slate-800 rounded-full overflow-hidden border border-white/5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${tf.score}%` }}
                transition={{ duration: 1, ease: "easeOut", delay: 0.2 + (i * 0.1) }}
                className={`absolute top-0 left-0 h-full ${
                  tf.score > 60 ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]' : 
                  tf.score < 40 ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 
                  'bg-gold-500 shadow-[0_0_10px_rgba(234,179,8,0.5)]'
                }`}
              />
            </div>
            
            <div className={`w-24 text-right text-xs font-bold ${
              tf.score > 60 ? 'text-green-400' : 
              tf.score < 40 ? 'text-red-400' : 'text-gold-400'
            }`}>
              {tf.signal}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
