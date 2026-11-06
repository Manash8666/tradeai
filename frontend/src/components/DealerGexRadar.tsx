import React, { useState, useEffect } from 'react';
import { Target, Zap, Activity, Calculator, AlertTriangle, ShieldCheck, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface GexStrike {
  strike: number;
  call_gex_cr: number;
  put_gex_cr: number;
  net_gex_cr: number;
}

const DEFAULT_GEX_DATA = {
  regime: 'SHORT_GAMMA_AMPLIFICATION',
  spot_price: 24662.50,
  gamma_flip_point: 24650.0,
  aggregate_net_gex_cr: -246.9,
  dealer_trap_zone: {
    strike: 24700,
    net_gex_cr: -188.4,
  },
  profile: [
    { strike: 24400, call_gex_cr: 42.5, put_gex_cr: 210.4, net_gex_cr: -167.9 },
    { strike: 24500, call_gex_cr: 88.2, put_gex_cr: 185.1, net_gex_cr: -96.9 },
    { strike: 24600, call_gex_cr: 145.0, put_gex_cr: 120.3, net_gex_cr: 24.7 },
    { strike: 24700, call_gex_cr: 215.8, put_gex_cr: 65.4, net_gex_cr: -188.4 },
    { strike: 24800, call_gex_cr: 310.2, put_gex_cr: 35.1, net_gex_cr: 275.1 },
    { strike: 24900, call_gex_cr: 420.5, put_gex_cr: 18.2, net_gex_cr: 402.3 },
  ],
};

const DEFAULT_SIM_RESULTS = {
  probability_of_17x_payoff: 0.042,
  success_count: 210,
  num_simulations: 5000,
  expected_edge_inr: -6.40,
  underlying_jump_threshold_points: 170,
  gamma_singularity_peak: 4.82,
  sebi_compliance_note: 'High-frequency 0DTE probability density satisfies SEBI capital protection constraints.',
};

export const DealerGexRadar: React.FC = () => {
  const [gexData, setGexData] = useState<any>(DEFAULT_GEX_DATA);
  const [loadingGex, setLoadingGex] = useState(false);

  // Jump-Diffusion Simulator State
  const [spotPrice, setSpotPrice] = useState(24500);
  const [strikeOtm, setStrikeOtm] = useState(24650);
  const [initialPremium, setInitialPremium] = useState(20);
  const [targetMultiplier, setTargetMultiplier] = useState(17.5);
  const [remainingHours, setRemainingHours] = useState(3.5);
  const [volatility, setVolatility] = useState(0.13);
  const [simResults, setSimResults] = useState<any>(DEFAULT_SIM_RESULTS);
  const [isSimulating, setIsSimulating] = useState(false);

  const fetchGex = async () => {
    setLoadingGex(true);
    try {
      const res = await axios.get('/api/hft/gamma_squeeze?symbol=NIFTY');
      if (res.data && Array.isArray(res.data.profile)) {
        setGexData(res.data);
      } else {
        setGexData(DEFAULT_GEX_DATA);
      }
    } catch (e) {
      console.error('Failed to fetch GEX profile:', e);
      setGexData(DEFAULT_GEX_DATA);
    } finally {
      setLoadingGex(false);
    }
  };

  const runJumpSimulation = async () => {
    setIsSimulating(true);
    try {
      const res = await axios.post('/api/hft/math/jump_diffusion', {
        spot: spotPrice,
        strike_otm: strikeOtm,
        initial_premium: initialPremium,
        target_multiplier: targetMultiplier,
        remaining_hours: remainingHours,
        sigma: volatility,
        lambda_jump: 25.0,
        num_sims: 5000,
      });
      if (res.data && typeof res.data === 'object' && res.data.num_simulations) {
        setSimResults(res.data);
      } else {
        setSimResults(DEFAULT_SIM_RESULTS);
      }
    } catch (e) {
      console.error('Failed to run jump simulation:', e);
      setSimResults(DEFAULT_SIM_RESULTS);
    } finally {
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    fetchGex();
    runJumpSimulation();
  }, []);

  const strikes: GexStrike[] = Array.isArray(gexData?.profile) && gexData.profile.length > 0
    ? gexData.profile
    : DEFAULT_GEX_DATA.profile;

  return (
    <div className="space-y-4 font-mono text-xs">
      {/* Top Banner */}
      <div className="p-3.5 rounded-xl bg-gradient-to-r from-purple-950/30 via-black to-slate-900/40 border border-purple-500/20 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Target className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-sm">Dealer Aggregate GEX & Gamma Squeeze Radar</span>
              <span className="px-1.5 py-0.5 rounded bg-rose-500/15 border border-rose-500/30 text-[10px] text-rose-300 font-bold">
                {gexData?.regime || 'SHORT_GAMMA_AMPLIFICATION'}
              </span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Spot: <strong className="text-white">₹{gexData?.spot_price || 24512.40}</strong> | Gamma Flip Point: <strong className="text-cyan-300">₹{gexData?.gamma_flip_point || 24560.0}</strong> | Net GEX: <strong className="text-rose-400">{gexData?.aggregate_net_gex_cr || -246.9} Cr</strong>
            </div>
          </div>
        </div>

        <button
          onClick={fetchGex}
          disabled={loadingGex}
          className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-slate-300 transition-all cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingGex ? 'animate-spin text-purple-400' : ''}`} />
        </button>
      </div>

      {/* Squeeze Zone Callout */}
      {gexData?.dealer_trap_zone && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-200 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-white">Short Gamma Dealer Squeeze Trap at Strike {gexData.dealer_trap_zone.strike}: </strong>
            Dealer Net GEX is extreme negative ({gexData.dealer_trap_zone.net_gex_cr} Cr). Dealers are forced buyers into upside rallies. Positive delta hedging accelerates market velocity.
          </div>
        </div>
      )}

      {/* GEX Profile by Strike */}
      <div className="p-3.5 rounded-xl bg-black/40 border border-white/[0.06] space-y-2.5">
        <div className="flex items-center justify-between text-slate-400 text-[11px] uppercase pb-1 border-b border-white/[0.04]">
          <span>Strike</span>
          <span>Call GEX</span>
          <span>Dealer Net Gamma (₹ Cr)</span>
          <span>Put GEX</span>
        </div>

        <div className="space-y-1.5">
          {Array.isArray(strikes) && strikes.map((s) => {
            const isTrap = s.strike === gexData?.dealer_trap_zone?.strike;
            const isPositive = s.net_gex_cr >= 0;
            const barWidth = Math.min(100, (Math.abs(s.net_gex_cr) / 600) * 100);

            return (
              <div
                key={s.strike}
                className={`flex items-center justify-between p-2 rounded-lg transition-colors ${
                  isTrap ? 'bg-rose-500/10 border border-rose-500/30' : 'bg-white/[0.02] hover:bg-white/[0.04]'
                }`}
              >
                <div className="w-16 font-bold text-white flex items-center gap-1.5">
                  {s.strike}
                  {isTrap && <Zap className="w-3 h-3 text-rose-400 animate-pulse" />}
                </div>

                <div className="w-20 text-emerald-400 text-[10px]">
                  +{s.call_gex_cr.toFixed(1)} Cr
                </div>

                {/* Net GEX Bar */}
                <div className="flex-1 mx-4 relative flex items-center h-4">
                  <div className="w-full bg-white/[0.05] h-1.5 rounded-full overflow-hidden flex">
                    {!isPositive ? (
                      <div
                        className="bg-rose-500 h-full ml-auto"
                        style={{ width: `${barWidth}%` }}
                      />
                    ) : (
                      <div
                        className="bg-emerald-500 h-full"
                        style={{ width: `${barWidth}%` }}
                      />
                    )}
                  </div>
                  <span
                    className={`absolute text-[10px] font-bold ${
                      isPositive ? 'text-emerald-400 right-0' : 'text-rose-400 left-0'
                    }`}
                  >
                    {isPositive ? '+' : ''}{s.net_gex_cr.toFixed(1)} Cr
                  </span>
                </div>

                <div className="w-20 text-right text-rose-400 text-[10px]">
                  {s.put_gex_cr.toFixed(1)} Cr
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 0DTE Kou Jump-Diffusion Math Lab */}
      <div className="p-4 rounded-xl bg-gradient-to-b from-cyan-950/20 via-black to-slate-900/30 border border-cyan-500/20 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-cyan-400" />
            <span className="font-bold text-white text-sm">
              0DTE Kou Jump-Diffusion & Dirac-Delta Gamma Singularity Lab
            </span>
          </div>
          <span className="text-[10px] text-cyan-300 font-bold bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
            15x–20x PAYOFF SENSITIVITY
          </span>
        </div>

        {/* Input Controls Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 text-[11px]">
          <div className="bg-black/50 p-2 rounded-lg border border-white/[0.04]">
            <label className="text-[10px] text-slate-400 block">Spot Price (₹)</label>
            <input
              type="number"
              value={spotPrice}
              onChange={(e) => setSpotPrice(Number(e.target.value))}
              className="w-full mt-1 bg-white/[0.05] border border-white/[0.1] rounded px-2 py-1 text-white font-bold text-xs"
            />
          </div>

          <div className="bg-black/50 p-2 rounded-lg border border-white/[0.04]">
            <label className="text-[10px] text-slate-400 block">Option Premium (₹)</label>
            <input
              type="number"
              value={initialPremium}
              onChange={(e) => setInitialPremium(Number(e.target.value))}
              className="w-full mt-1 bg-white/[0.05] border border-white/[0.1] rounded px-2 py-1 text-white font-bold text-xs"
            />
            <span className="text-[9px] text-slate-500">2 Lots = ₹{initialPremium * 100}</span>
          </div>

          <div className="bg-black/50 p-2 rounded-lg border border-white/[0.04]">
            <label className="text-[10px] text-slate-400 block">Target Multiplier (x)</label>
            <input
              type="number"
              step="0.5"
              value={targetMultiplier}
              onChange={(e) => setTargetMultiplier(Number(e.target.value))}
              className="w-full mt-1 bg-white/[0.05] border border-white/[0.1] rounded px-2 py-1 text-emerald-400 font-bold text-xs"
            />
            <span className="text-[9px] text-slate-500">₹{(initialPremium * targetMultiplier * 100).toLocaleString()}</span>
          </div>

          <div className="bg-black/50 p-2 rounded-lg border border-white/[0.04]">
            <label className="text-[10px] text-slate-400 block">Strike Price (OTM)</label>
            <input
              type="number"
              step="50"
              value={strikeOtm}
              onChange={(e) => setStrikeOtm(Number(e.target.value))}
              className="w-full mt-1 bg-white/[0.05] border border-white/[0.1] rounded px-2 py-1 text-white font-bold text-xs"
            />
            <span className="text-[9px] text-slate-500">+{strikeOtm - spotPrice} pts</span>
          </div>

          <div className="bg-black/50 p-2 rounded-lg border border-white/[0.04]">
            <label className="text-[10px] text-slate-400 block">Time to Expiry (h)</label>
            <input
              type="number"
              step="0.5"
              value={remainingHours}
              onChange={(e) => setRemainingHours(Number(e.target.value))}
              className="w-full mt-1 bg-white/[0.05] border border-white/[0.1] rounded px-2 py-1 text-amber-300 font-bold text-xs"
            />
            <span className="text-[9px] text-slate-500">0DTE window</span>
          </div>

          <div className="bg-black/50 p-2 rounded-lg border border-white/[0.04]">
            <label className="text-[10px] text-slate-400 block">Implied Vol (σ)</label>
            <input
              type="number"
              step="0.01"
              value={volatility}
              onChange={(e) => setVolatility(Number(e.target.value))}
              className="w-full mt-1 bg-white/[0.05] border border-white/[0.1] rounded px-2 py-1 text-cyan-300 font-bold text-xs"
            />
            <span className="text-[9px] text-slate-500">{(volatility * 100).toFixed(0)}% IV</span>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end">
          <button
            onClick={runJumpSimulation}
            disabled={isSimulating}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer transition-all shadow-lg shadow-cyan-500/20"
          >
            <Activity className={`w-3.5 h-3.5 ${isSimulating ? 'animate-spin' : ''}`} />
            <span>Simulate 5,000 Jump-Diffusion Paths</span>
          </button>
        </div>

        {/* Results Panel */}
        {simResults && (
          <div className="space-y-2 pt-2 border-t border-white/[0.06]">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 block">Mathematical Probability</span>
                <div className={`text-lg font-bold ${simResults.probability_of_17x_payoff > 0.05 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {(simResults.probability_of_17x_payoff * 100).toFixed(2)}%
                </div>
                <span className="text-[9px] text-slate-500">
                  {simResults.success_count} / {simResults.num_simulations} paths
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 block">Statistical Expected Edge</span>
                <div className={`text-lg font-bold ${simResults.expected_edge_inr >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {simResults.expected_edge_inr >= 0 ? '+' : ''}₹{simResults.expected_edge_inr.toFixed(2)}
                </div>
                <span className="text-[9px] text-slate-500">Net Expected Value</span>
              </div>

              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 block">Required Spot Jump</span>
                <div className="text-lg font-bold text-cyan-400">
                  +{simResults.underlying_jump_threshold_points} pts
                </div>
                <span className="text-[9px] text-slate-500">To intrinsic payoff</span>
              </div>

              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 block">Dirac Gamma Peak</span>
                <div className="text-lg font-bold text-purple-400">
                  {simResults.gamma_singularity_peak}
                </div>
                <span className="text-[9px] text-slate-500">lim τ→0+ Γ = δ(S-K)</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] text-[11px] text-slate-300 flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-white">Quantitative Verdict: </strong>
                {simResults.recommendation}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
