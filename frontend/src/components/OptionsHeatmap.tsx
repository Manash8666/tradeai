import { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

interface OptionHeatmapProps {
  symbol?: string;
}

export function OptionsHeatmap({ symbol = 'NIFTY50' }: OptionHeatmapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let offset = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const cols = 48;
      const rows = 18;
      const cellW = canvas.width / cols;
      const cellH = canvas.height / rows;

      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          const noise = Math.sin(i * 0.12 + offset) * Math.cos(j * 0.18 + offset);
          const normalized = (noise + 1) / 2;

          let r = 0, g = 255, b = 136; // Emerald #00ff88
          let alpha = normalized * 0.75;
          if (normalized > 0.6) {
            // Hot Call Skew - Electric Cyan
            r = 56; g = 189; b = 248;
          } else if (normalized < 0.3) {
            // Put Skew - Radiant Crimson/Rose
            r = 255; g = 51; b = 102;
            alpha = (1 - normalized) * 0.7;
          }

          ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
          ctx.fillRect(i * cellW + 1, j * cellH + 1, cellW - 2, cellH - 2);
        }
      }

      offset += 0.03;
      animationId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="p-5 rounded-2xl border border-white/[0.08] bg-[#0c1017]/90 backdrop-blur-xl shadow-2xl flex flex-col"
    >
      <div className="flex justify-between items-center mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse" />
            <h2 className="text-base font-bold text-white font-syne tracking-wide">
              {symbol} LIVE OPTIONS OPEN INTEREST HEATMAP
            </h2>
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-0.5">
            50-STRIKE LIQUIDITY MATRIX · REAL-TIME IV SKEW FLOW
          </p>
        </div>
        <div className="flex gap-2 text-[10px] font-mono">
          <span className="px-2.5 py-1 rounded-md bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/20">
            CALL VOL SKEW
          </span>
          <span className="px-2.5 py-1 rounded-md bg-[#38bdf8]/10 text-[#38bdf8] border border-[#38bdf8]/20">
            ATM CONCENTRATION
          </span>
          <span className="px-2.5 py-1 rounded-md bg-[#ff3366]/10 text-[#ff3366] border border-[#ff3366]/20">
            PUT OI BUILDUP
          </span>
        </div>
      </div>

      <div className="flex-1 w-full bg-[#06080c] rounded-xl overflow-hidden border border-white/[0.06] relative">
        <canvas
          ref={canvasRef}
          width={800}
          height={260}
          className="w-full h-full object-cover"
        />
        <div className="absolute bottom-2 left-0 w-full flex justify-between px-4 text-[10px] text-slate-400 font-mono pointer-events-none bg-gradient-to-t from-black/80 to-transparent pt-3">
          <span>← DEEP ITM CALLS</span>
          <span className="text-[#38bdf8] font-bold">ATM (23,800)</span>
          <span>DEEP OTM PUTS →</span>
        </div>
      </div>
    </motion.div>
  );
}
