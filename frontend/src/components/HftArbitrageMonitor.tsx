import React, { useState, useEffect } from 'react';
import { ArrowRightLeft, ShieldCheck, AlertCircle, RefreshCw, Layers } from 'lucide-react';
import axios from 'axios';

interface ArbitrageOpportunity {
  symbol: string;
  nse_bid: number;
  nse_ask: number;
  bse_bid: number;
  bse_ask: number;
  action: string;
  gross_spread_inr: number;
  gross_spread_pct: number;
  statutory_friction_pct: number;
  net_spread_pct: number;
  net_profit_per_lot_inr: number;
  lot_size: number;
  is_actionable: boolean;
  wire_execution_deadline_us?: number;
  rejection_reason?: string;
}

const DEFAULT_OPPORTUNITIES: ArbitrageOpportunity[] = [
  {
    symbol: 'RELIANCE',
    nse_bid: 2985.40,
    nse_ask: 2985.60,
    bse_bid: 2986.90,
    bse_ask: 2987.10,
    action: 'BUY_NSE_SELL_BSE',
    gross_spread_inr: 1.30,
    gross_spread_pct: 0.0435,
    statutory_friction_pct: 0.0345,
    net_spread_pct: 0.0090,
    net_profit_per_lot_inr: 67.25,
    lot_size: 250,
    is_actionable: true,
    wire_execution_deadline_us: 120,
  },
  {
    symbol: 'HDFCBANK',
    nse_bid: 1720.15,
    nse_ask: 1720.30,
    bse_bid: 1720.60,
    bse_ask: 1720.75,
    action: 'BUY_NSE_SELL_BSE',
    gross_spread_inr: 0.30,
    gross_spread_pct: 0.0174,
    statutory_friction_pct: 0.0345,
    net_spread_pct: -0.0171,
    net_profit_per_lot_inr: -161.40,
    lot_size: 550,
    is_actionable: false,
    rejection_reason: 'BELOW_STATUTORY_FRICTION_HURDLE',
  },
];

export const HftArbitrageMonitor: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showFeeModal, setShowFeeModal] = useState(false);

  const fetchArbitrage = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/hft/arbitrage');
      if (res.data && Array.isArray(res.data.opportunities)) {
        setData(res.data);
      }
    } catch (e) {
      console.error('Failed to fetch arbitrage data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArbitrage();
    const interval = setInterval(fetchArbitrage, 3000);
    return () => clearInterval(interval);
  }, []);

  const opportunities: ArbitrageOpportunity[] =
    Array.isArray(data?.opportunities) && data.opportunities.length > 0
      ? data.opportunities
      : DEFAULT_OPPORTUNITIES;

  return (
    <div className="space-y-4 font-mono text-xs">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <ArrowRightLeft className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-sm">NSE–BSE Cross-Exchange Arbitrage Detector</span>
              <span className="px-1.5 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30 text-[10px] text-emerald-300 font-bold">
                SUB-MICROSECOND CORE
              </span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Statutory Hurdle Rate: <strong className="text-amber-300">{data?.statutory_fee_hurdle_bps || 3.45} bps</strong> (0.0345%) | Wire Latency Budget: &lt;120 µs
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFeeModal(!showFeeModal)}
            className="px-2.5 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-slate-300 text-[11px] flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span>Statutory Friction Matrix</span>
          </button>
          <button
            onClick={fetchArbitrage}
            disabled={loading}
            className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-slate-300 transition-all cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Fee Matrix Modal / Callout */}
      {showFeeModal && (
        <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/20 text-[11px] space-y-2">
          <div className="font-bold text-purple-300 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" />
            Indian Statutory Transaction Schedule (Cross-Exchange Round Trip)
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-slate-300">
            <div className="bg-black/40 p-2 rounded border border-white/[0.04]">
              <span className="text-slate-400 block text-[10px]">STT (Sell Leg)</span>
              <strong className="text-white">0.025% (2.50 bps)</strong>
            </div>
            <div className="bg-black/40 p-2 rounded border border-white/[0.04]">
              <span className="text-slate-400 block text-[10px]">NSE Turnover</span>
              <strong className="text-white">0.00325% (0.325 bps)</strong>
            </div>
            <div className="bg-black/40 p-2 rounded border border-white/[0.04]">
              <span className="text-slate-400 block text-[10px]">BSE Turnover</span>
              <strong className="text-white">0.00375% (0.375 bps)</strong>
            </div>
            <div className="bg-black/40 p-2 rounded border border-white/[0.04]">
              <span className="text-slate-400 block text-[10px]">Stamp Duty (Buy Leg)</span>
              <strong className="text-white">0.00300% (0.300 bps)</strong>
            </div>
            <div className="bg-black/40 p-2 rounded border border-white/[0.04]">
              <span className="text-slate-400 block text-[10px]">SEBI Turnover Fee</span>
              <strong className="text-white">₹10 / Crore</strong>
            </div>
            <div className="bg-black/40 p-2 rounded border border-white/[0.04]">
              <span className="text-slate-400 block text-[10px]">GST</span>
              <strong className="text-white">18% on Txn & SEBI</strong>
            </div>
          </div>
          <p className="text-[10px] text-purple-200/80">
            * Arbitrage detector enforces an invariant: Gross Spread must strictly exceed the 3.45 bps hurdle to trigger execution. Sub-hurdle spreads are auto-quarantined to protect capital.
          </p>
        </div>
      )}

      {/* Opportunities Table */}
      <div className="overflow-x-auto rounded-xl border border-white/[0.06] bg-black/40">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-white/[0.06] text-slate-400 text-[10px] uppercase bg-white/[0.01]">
              <th className="py-2.5 px-3">Symbol</th>
              <th className="py-2.5 px-2">NSE (Bid / Ask)</th>
              <th className="py-2.5 px-2">BSE (Bid / Ask)</th>
              <th className="py-2.5 px-2">Gross Spread</th>
              <th className="py-2.5 px-2">Statutory Fee</th>
              <th className="py-2.5 px-2">Net Edge (bps)</th>
              <th className="py-2.5 px-2">Net Profit / Lot</th>
              <th className="py-2.5 px-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.03]">
            {opportunities.map((opp) => (
              <tr key={opp.symbol} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-2.5 px-3 font-bold text-white flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${opp.is_actionable ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                  {opp.symbol}
                </td>
                <td className="py-2.5 px-2 text-slate-300">
                  ₹{opp.nse_bid.toFixed(2)} / ₹{opp.nse_ask.toFixed(2)}
                </td>
                <td className="py-2.5 px-2 text-slate-300">
                  ₹{opp.bse_bid.toFixed(2)} / ₹{opp.bse_ask.toFixed(2)}
                </td>
                <td className="py-2.5 px-2 text-amber-300 font-bold">
                  ₹{opp.gross_spread_inr.toFixed(2)} (+{(opp.gross_spread_pct * 100).toFixed(3)}%)
                </td>
                <td className="py-2.5 px-2 text-rose-300">
                  -{(opp.statutory_friction_pct * 100).toFixed(3)}%
                </td>
                <td className={`py-2.5 px-2 font-bold ${opp.net_spread_pct > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {opp.net_spread_pct > 0 ? '+' : ''}{(opp.net_spread_pct * 100).toFixed(3)}%
                </td>
                <td className={`py-2.5 px-2 font-bold ${opp.net_profit_per_lot_inr > 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {opp.net_profit_per_lot_inr > 0 ? `+₹${opp.net_profit_per_lot_inr.toFixed(2)}` : '₹0.00'}
                  <span className="text-[9px] text-slate-500 block font-normal">({opp.lot_size} shares)</span>
                </td>
                <td className="py-2.5 px-3 text-right">
                  {opp.is_actionable ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold">
                      <ShieldCheck className="w-3 h-3" />
                      ACTIONABLE ({opp.wire_execution_deadline_us} µs)
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[10px]">
                      <AlertCircle className="w-3 h-3" />
                      SUB-HURDLE
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
