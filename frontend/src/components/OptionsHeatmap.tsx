import { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

interface OptionHeatmapProps {
  symbol?: string;
}

export function OptionsHeatmap({ symbol = 'NIFTY50' }: OptionHeatmapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const workerRef = useRef<Worker | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Use OffscreenCanvas API natively off the main thread
    const offscreen = canvas.transferControlToOffscreen();
    workerRef.current = new Worker(new URL('../workers/heatmap.worker.ts', import.meta.url), { type: 'module' });
    
    // Pass control to the Worker thread
    workerRef.current.postMessage({ type: 'init', canvas: offscreen }, [offscreen]);

    return () => {
      if (workerRef.current) {
        workerRef.current.postMessage({ type: 'cleanup' });
        workerRef.current.terminate();
      }
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.7 }}
      className="glass-panel p-6 h-full flex flex-col"
    >
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-bold bg-gradient-to-r from-gold-200 to-gold-400 bg-clip-text text-transparent">
            {symbol} Options Flow Map
          </h2>
          <p className="text-xs text-ocean-200 font-mono mt-1">REAL-TIME OPEN INTEREST CANVAS API</p>
        </div>
        <div className="flex gap-2 text-xs font-mono">
          <span className="px-2 py-1 bg-white/5 rounded text-gold-200">CALL SKEW</span>
          <span className="px-2 py-1 bg-white/5 rounded text-ocean-300">PUT SKEW</span>
        </div>
      </div>
      
      <div className="flex-1 w-full bg-slate-900/50 rounded-lg overflow-hidden border border-white/5 relative">
        <canvas 
          ref={canvasRef}
          width={800} 
          height={300}
          className="w-full h-full object-cover mix-blend-screen"
        />
        {/* Synthetic X-Axis for aesthetics */}
        <div className="absolute bottom-2 left-0 w-full flex justify-between px-4 text-[10px] text-ocean-300/50 font-mono">
          <span>ITM CALLS</span>
          <span>ATM</span>
          <span>OTM PUTS</span>
        </div>
      </div>
    </motion.div>
  );
}
