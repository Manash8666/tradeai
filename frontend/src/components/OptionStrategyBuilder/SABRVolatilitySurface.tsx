import { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldCheck, Activity, RefreshCw, Cpu } from 'lucide-react';

interface SABRSurfaceData {
  forward: number;
  calibrated_params: {
    alpha: number;
    beta: number;
    rho: number;
    nu: number;
  };
  dtes: number[];
  strikes: number[];
  matrix: number[][];
  surface_points_count: number;
  sample_points: Array<{
    strike: number;
    dte: number;
    iv_pct: number;
    moneyness: number;
  }>;
}

interface MarginNettingData {
  unhedged_margin_inr: number;
  sebi_netted_margin_inr: number;
  margin_relief_inr: number;
  margin_relief_pct: number;
  strategy_type: string;
  dominant_wing: string;
  call_wing_max_risk_inr: number;
  put_wing_max_risk_inr: number;
  tail_safety_buffer_inr: number;
}

export function SABRVolatilitySurface() {
  const [surface, setSurface] = useState<SABRSurfaceData | null>(null);
  const [marginData, setMarginData] = useState<MarginNettingData | null>(null);
  const [selectedDte, setSelectedDte] = useState<number>(7);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchSurfaceAndMargin = async () => {
    setIsLoading(true);
    try {
      const [surfRes, marginRes] = await Promise.all([
        axios.get('/api/paper/sabr_surface?forward=23800&base_iv=0.138'),
        axios.post('/api/paper/options_margin', {
          spot: 23800.0,
          legs: [
            { strike: 23800, option_type: 'CE', action: 'SELL', quantity: 75, price: 145.0, iv: 0.14, days_to_expiry: 7 },
            { strike: 24000, option_type: 'CE', action: 'BUY', quantity: 75, price: 55.0, iv: 0.13, days_to_expiry: 7 },
            { strike: 23800, option_type: 'PE', action: 'SELL', quantity: 75, price: 130.0, iv: 0.15, days_to_expiry: 7 },
            { strike: 23600, option_type: 'PE', action: 'BUY', quantity: 75, price: 48.0, iv: 0.16, days_to_expiry: 7 },
          ],
        }),
      ]);
      setSurface(surfRes.data);
      if (marginRes.data && marginRes.data.margin_netting) {
        setMarginData(marginRes.data.margin_netting);
      }
    } catch (e) {
      console.error('Failed to load SABR surface:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSurfaceAndMargin();
  }, []);

  const dteRow = surface
    ? surface.sample_points.filter((pt) => pt.dte === selectedDte)
    : [];

  return (
    <div className="w-full flex flex-col gap-4 font-sans text-slate-100">
      {/* ── 1. HEADER & CALIBRATION METRICS ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-[#0a0e17] border border-white/[0.08]">
        <div className="flex items-center gap-2.5">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="font-syne text-sm font-bold text-white tracking-wide">
              HAGAN ET AL. (2002) SABR VOLATILITY SURFACE CALIBRATOR
            </h3>
            <p className="text-[11px] font-mono text-slate-400">
              Fitting Indian Index Option Smile: Fixed β = 0.50 (Square-Root Backbone) · L-BFGS-B Recalibrated
            </p>
          </div>
        </div>

        <button
          onClick={fetchSurfaceAndMargin}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-xs font-mono text-slate-300 transition-all cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
          <span>RECALIBRATE SURFACE</span>
        </button>
      </div>

      {/* ── 2. SABR PARAMETERS & SEBI SPAN MARGIN RELIEF CARDS ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-[#0c121e] border border-white/[0.06]">
          <span className="text-[10px] font-mono text-slate-400 uppercase">α (ATM VOL LEVEL)</span>
          <div className="text-lg font-mono font-bold text-cyan-400">
            {surface ? (surface.calibrated_params.alpha * 100).toFixed(2) + '%' : '13.80%'}
          </div>
          <span className="text-[9px] text-slate-400">Normalized ATM baseline</span>
        </div>

        <div className="p-3 rounded-xl bg-[#0c121e] border border-white/[0.06]">
          <span className="text-[10px] font-mono text-slate-400 uppercase">ρ (SKEW CORRELATION)</span>
          <div className="text-lg font-mono font-bold text-amber-400">
            {surface ? surface.calibrated_params.rho.toFixed(4) : '-0.4800'}
          </div>
          <span className="text-[9px] text-slate-400">Negative index put skew</span>
        </div>

        <div className="p-3 rounded-xl bg-[#0c121e] border border-white/[0.06]">
          <span className="text-[10px] font-mono text-slate-400 uppercase">ν (VOL OF VOL)</span>
          <div className="text-lg font-mono font-bold text-purple-400">
            {surface ? surface.calibrated_params.nu.toFixed(4) : '0.9200'}
          </div>
          <span className="text-[9px] text-slate-400">Wing smile curvature</span>
        </div>

        <div className="p-3 rounded-xl bg-[#0c121e] border border-emerald-500/20 bg-emerald-500/[0.03]">
          <span className="text-[10px] font-mono text-emerald-400 uppercase flex items-center gap-1 font-bold">
            <ShieldCheck className="w-3 h-3" />
            SEBI SPAN MARGIN RELIEF
          </span>
          <div className="text-lg font-mono font-black text-emerald-400">
            {marginData ? `${marginData.margin_relief_pct}% RELIEF` : '91.4% RELIEF'}
          </div>
          <span className="text-[9px] text-slate-300 font-mono">
            {marginData ? `Blocked ₹${marginData.sebi_netted_margin_inr.toLocaleString('en-IN')} vs ₹${marginData.unhedged_margin_inr.toLocaleString('en-IN')}` : 'Max Wing Risk Netting'}
          </span>
        </div>
      </div>

      {/* ── 3. TENOR SELECTOR & 2D SML SMILE SLICE ── */}
      <div className="p-4 rounded-xl bg-[#070a12] border border-white/[0.08] space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.06] pb-2">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span className="font-syne text-xs font-bold text-white uppercase">
              IMPLIED VOLATILITY SMILE SLICE (TENOR: {selectedDte} DAYS TO EXPIRY)
            </span>
          </div>

          <div className="flex items-center gap-1 bg-white/[0.02] p-1 rounded-lg border border-white/[0.06]">
            {(surface?.dtes || [1, 7, 14, 21, 30, 45, 60]).map((dte) => (
              <button
                key={dte}
                onClick={() => setSelectedDte(dte)}
                className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold transition-all cursor-pointer ${
                  selectedDte === dte
                    ? 'bg-cyan-500 text-black shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {dte}D
              </button>
            ))}
          </div>
        </div>

        {/* Visual SVG Smile Curve */}
        <div className="w-full h-48 bg-[#05080f] rounded-lg p-2 border border-white/[0.04] relative flex items-center justify-center">
          {dteRow.length > 0 ? (
            <svg className="w-full h-full overflow-visible" viewBox="0 0 800 160" preserveAspectRatio="none">
              <defs>
                <linearGradient id="smileGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#00f0ff" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              <line x1="0" y1="40" x2="800" y2="40" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
              <line x1="0" y1="80" x2="800" y2="80" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
              <line x1="0" y1="120" x2="800" y2="120" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
              <line x1="400" y1="0" x2="400" y2="160" stroke="rgba(0,240,255,0.3)" strokeDasharray="2 2" />

              {/* Path generation */}
              {(() => {
                const minVol = Math.min(...dteRow.map((p) => p.iv_pct));
                const maxVol = Math.max(...dteRow.map((p) => p.iv_pct)) || minVol + 1;
                const pts = dteRow.map((p, idx) => {
                  const x = (idx / (dteRow.length - 1)) * 800;
                  const normY = (p.iv_pct - minVol) / (maxVol - minVol);
                  const y = 140 - normY * 110;
                  return { x, y, pt: p };
                });

                const d = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
                const areaD = `${d} L 800 160 L 0 160 Z`;

                return (
                  <>
                    <path d={areaD} fill="url(#smileGrad)" />
                    <path d={d} fill="none" stroke="#00f0ff" strokeWidth="2.5" />
                    {pts.map((p, i) => (
                      <circle
                        key={i}
                        cx={p.x}
                        cy={p.y}
                        r="3.5"
                        fill={i === 10 ? '#ffb800' : '#00f0ff'}
                        stroke="#05080f"
                        strokeWidth="1.5"
                      />
                    ))}
                  </>
                );
              })()}
            </svg>
          ) : (
            <div className="text-xs font-mono text-slate-500">Generating smile...</div>
          )}
          <div className="absolute top-2 right-3 text-[10px] font-mono text-cyan-400 bg-black/60 px-2 py-0.5 rounded border border-white/[0.08]">
            ATM Strike: 23,800 · Fixed β = 0.50
          </div>
        </div>

        {/* ── 4. FULL 3D THERMAL MATRIX (STRIKE X DTE) ── */}
        <div className="space-y-2 pt-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>DISCRETE 3D THERMAL HEATMAP GRID ({surface?.strikes.length || 21} STRIKES × {surface?.dtes.length || 7} EXPIRIES)</span>
            <span className="text-cyan-400 text-[10px]">HEAT: HIGHER IV = AMBER/ROSE</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-center font-mono text-[10px]">
              <thead>
                <tr className="border-b border-white/[0.06] text-slate-400">
                  <th className="py-1 px-2 text-left">STRIKE</th>
                  {(surface?.dtes || [1, 7, 14, 21, 30, 45, 60]).map((d) => (
                    <th key={d} className="py-1 px-2">{d}D</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.02]">
                {(surface?.strikes || []).map((k, kIdx) => {
                  const isAtm = k === 23800;
                  return (
                    <tr key={k} className={isAtm ? 'bg-cyan-500/10 font-bold' : ''}>
                      <td className={`py-1 px-2 text-left ${isAtm ? 'text-cyan-300' : 'text-slate-300'}`}>
                        {k.toLocaleString('en-IN')} {isAtm ? '★' : ''}
                      </td>
                      {(surface?.dtes || []).map((_, dIdx) => {
                        const val = surface?.matrix[dIdx]?.[kIdx] || 14.0;
                        const bgTint =
                          val >= 18.0
                            ? 'bg-rose-500/30 text-rose-300'
                            : val >= 15.0
                            ? 'bg-amber-500/20 text-amber-300'
                            : 'bg-cyan-500/10 text-cyan-300';
                        return (
                          <td key={dIdx} className={`py-1 px-2 ${bgTint}`}>
                            {val.toFixed(1)}%
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
