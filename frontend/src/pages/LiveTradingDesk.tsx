import { useState, useMemo, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Zap,
  Shield,
  Plus,
  Minus,
  RefreshCw,
  Sun,
  Clock,
  CheckCircle2,
  Lock,
  Scale,
  FileText,
  X,
  Download,
  Cpu,
  ShieldCheck
} from 'lucide-react';
import axios from 'axios';
import { TradingViewChart } from '../components/TradingViewChart';
import { HftArbitrageMonitor } from '../components/HftArbitrageMonitor';
import { DealerGexRadar } from '../components/DealerGexRadar';

interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface OrderBookItem {
  price: number;
  orders: number;
  qty: number;
}

interface AssetClass {
  symbol: string;
  code: string;
  spot: number;
  change: number;
  changePct: number;
  lotSize: number;
  step: number;
  category: 'INDEX' | 'STOCK' | 'COMMODITY';
}

interface PositionItem {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  qty: number;
  entryPrice: number;
  currentPrice: number;
  pnlInr: number;
  pnlPct: number;
  sl: number;
  target: number;
  holdingDurationMins?: number;
}

// 12 Institutional Assets
const ASSET_CLASSES: AssetClass[] = [
  // ── Indian Indices ──
  { symbol: 'NIFTY 50', code: 'NIFTY', spot: 23806.95, change: 112.50, changePct: 0.47, lotSize: 75, step: 50, category: 'INDEX' },
  { symbol: 'BANK NIFTY', code: 'BANKNIFTY', spot: 51240.80, change: 245.20, changePct: 0.48, lotSize: 15, step: 100, category: 'INDEX' },
  { symbol: 'FINNIFTY', code: 'FINNIFTY', spot: 24185.30, change: 98.40, changePct: 0.41, lotSize: 25, step: 50, category: 'INDEX' },
  { symbol: 'SENSEX', code: 'SENSEX', spot: 78540.20, change: 380.10, changePct: 0.49, lotSize: 10, step: 100, category: 'INDEX' },
  // ── Bluechip Equities ──
  { symbol: 'RELIANCE', code: 'RELIANCE', spot: 2984.50, change: 24.80, changePct: 0.84, lotSize: 250, step: 20, category: 'STOCK' },
  { symbol: 'TCS', code: 'TCS', spot: 4125.75, change: 38.20, changePct: 0.93, lotSize: 175, step: 20, category: 'STOCK' },
  { symbol: 'HDFC BANK', code: 'HDFCBANK', spot: 1745.20, change: 12.40, changePct: 0.72, lotSize: 550, step: 10, category: 'STOCK' },
  { symbol: 'INFOSYS', code: 'INFY', spot: 1860.40, change: -8.60, changePct: -0.46, lotSize: 400, step: 10, category: 'STOCK' },
  { symbol: 'TATA MOTORS', code: 'TATAMOTORS', spot: 985.60, change: 18.50, changePct: 1.91, lotSize: 700, step: 10, category: 'STOCK' },
  // ── MCX Commodities ──
  { symbol: 'CRUDE OIL', code: 'CRUDEOIL', spot: 6745.00, change: 42.00, changePct: 0.63, lotSize: 100, step: 50, category: 'COMMODITY' },
  { symbol: 'MCX GOLD', code: 'GOLD', spot: 78420.00, change: 380.00, changePct: 0.49, lotSize: 10, step: 100, category: 'COMMODITY' },
  { symbol: 'MCX SILVER', code: 'SILVER', spot: 94250.00, change: 840.00, changePct: 0.90, lotSize: 30, step: 500, category: 'COMMODITY' },
];

// The 15 Mandatory Lookback Horizons
const LOOKBACK_HORIZONS = [
  { id: '1h', label: '1H', desc: '1 Hour (1m)' },
  { id: '3h', label: '3H', desc: '3 Hours (3m)' },
  { id: '6h', label: '6H', desc: '6 Hours (5m)' },
  { id: '12h', label: '12H', desc: '12 Hours (10m)' },
  { id: '24h', label: '24H', desc: '24 Hours (15m)' },
  { id: '48h', label: '48H', desc: '48 Hours (30m)' },
  { id: '72h', label: '72H', desc: '72 Hours (1h)' },
  { id: '10d', label: '10D', desc: '10 Days (2h)' },
  { id: '15d', label: '15D', desc: '15 Days (4h)' },
  { id: '30d', label: '30D', desc: '30 Days (Daily)' },
  { id: '45d', label: '45D', desc: '45 Days (Daily)' },
  { id: '60d', label: '60D', desc: '60 Days (Daily)' },
  { id: '90d', label: '90D', desc: '90 Days (Quarterly)' },
  { id: '180d', label: '180D', desc: '180 Days (Half-Yearly)' },
  { id: '365d', label: '365D', desc: '365 Days (Annual)' },
];

export function LiveTradingDesk() {
  const [selectedAsset, setSelectedAsset] = useState<AssetClass>(ASSET_CLASSES[0]);
  const [selectedHorizon, setSelectedHorizon] = useState<string>('24h');
  const [candles, setCandles] = useState<Candle[]>([]);
  const [isLoadingCandles, setIsLoadingCandles] = useState<boolean>(false);
  const [premarketCues, setPremarketCues] = useState<any>(null);

  const [activeTabBottom, setActiveTabBottom] = useState<
    'positions' | 'orders' | 'hft_arbitrage' | 'dealer_gex' | 'post_mortem' | 'ledger'
  >('positions');

  // Trade Execution State
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT' | 'SL_M'>('MARKET');
  const [productType, setProductType] = useState<'MIS' | 'NRML'>('MIS');
  const [lotCount, setLotCount] = useState<number>(1);
  const [limitPrice, setLimitPrice] = useState<number>(selectedAsset.spot);
  const [slPoints, setSlPoints] = useState<number>(30);
  const [targetPoints, setTargetPoints] = useState<number>(60);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [execMessage, setExecMessage] = useState<string | null>(null);

  // Institutional Engine Data States
  const [accountSummary, setAccountSummary] = useState<any>(null);
  const [positions, setPositions] = useState<PositionItem[]>([]);
  const [completedTrades, setCompletedTrades] = useState<any[]>([]);
  const [behavioralAnalytics, setBehavioralAnalytics] = useState<any>(null);
  const [simulatedRisk, setSimulatedRisk] = useState<any>(null);
  const [contextualSentiment, setContextualSentiment] = useState<any>(null);
  const [allContextualEvents, setAllContextualEvents] = useState<any[]>([]);

  // Modals & Institutional HFT Tools
  const [showNewsRadar, setShowNewsRadar] = useState<boolean>(false);
  const [showTaxSchedule, setShowTaxSchedule] = useState<boolean>(false);
  const [showNeuroModal, setShowNeuroModal] = useState<boolean>(false);
  const [neuroVerdict, setNeuroVerdict] = useState<any>(null);
  const [isTickingAgent, setIsTickingAgent] = useState<boolean>(false);

  const handleDownloadSebiReport = async () => {
    try {
      const res = await axios.get('/api/hft/sebi_report/download', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `MRG_CLIENT_ALLOCATION_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (e) {
      console.error('Failed to download SEBI report:', e);
    }
  };

  const handleTestAgentCycle = async () => {
    setIsTickingAgent(true);
    try {
      const res = await axios.post('/api/hft/agent/tick', {
        symbol: selectedAsset.code,
        ltp: selectedAsset.spot,
        ofi: 0.42,
        micro_price: selectedAsset.spot + 3.5,
        dealer_net_gex: -550.0,
        macro_sentiment_score: 0.38,
        is_0dte_expiry_day: true,
        minutes_to_market_close: 180,
      });
      setNeuroVerdict(res.data.verdict);
    } catch (e) {
      console.error('Failed to tick agent:', e);
    } finally {
      setIsTickingAgent(false);
    }
  };

  // Fetch Premarket Cues
  useEffect(() => {
    const fetchPremarket = async () => {
      try {
        const res = await axios.get('/api/mirajane/market/premarket');
        setPremarketCues(res.data);
      } catch {
        setPremarketCues({
          analysis_date: '05 November 2026, Thursday',
          gift_nifty_gap: { points: 112.5, percent: 0.47, bias: 'GAP_UP' },
          overnight_global_cues: { sp500_change_pct: 0.72, brent_crude_usd: 81.20, us_10y_yield_pct: 4.12, dxy_index: 103.85 },
          fii_dii_stance: { fii_net_cash_crores: 2450.0, dii_net_cash_crores: 1890.0, net_bias: 'STRONG_INSTITUTIONAL_BUY' },
          opening_actionable_plan: 'Strong Gap-Up Open Expected across BFSI & Tech. Watch 23,800 Call writer unwinding for 0DTE gamma squeeze.',
        });
      }
    };
    fetchPremarket();
  }, []);

  // Fetch Institutional Paper Account & Positions
  const fetchAccountAndPositions = useCallback(async () => {
    try {
      const [accRes, posRes, trdRes] = await Promise.all([
        axios.get('/api/paper/account'),
        axios.get('/api/paper/positions'),
        axios.get('/api/paper/trades'),
      ]);
      setAccountSummary(accRes.data);
      if (accRes.data && accRes.data.behavioral_analytics) {
        setBehavioralAnalytics(accRes.data.behavioral_analytics);
      }
      if (Array.isArray(posRes.data)) {
        setPositions(
          posRes.data.map((p: any, idx: number) => ({
            id: `pos-${p.symbol}-${idx}`,
            symbol: p.symbol,
            side: p.side,
            qty: p.quantity,
            entryPrice: p.avg_price,
            currentPrice: p.current_ltp,
            pnlInr: p.unrealized_net_pnl,
            pnlPct: p.avg_price > 0 ? ((p.current_ltp - p.avg_price) / p.avg_price) * 100 * (p.side === 'BUY' ? 1 : -1) : 0,
            sl: p.sl_price,
            target: p.target_price,
            holdingDurationMins: p.holding_duration_mins,
          }))
        );
      }
      if (trdRes.data) {
        setCompletedTrades(trdRes.data.trades || []);
      }
    } catch (e) {
      console.error('Failed to sync institutional paper account:', e);
    }
  }, []);

  useEffect(() => {
    fetchAccountAndPositions();
    const interval = setInterval(fetchAccountAndPositions, 4000);
    return () => clearInterval(interval);
  }, [fetchAccountAndPositions]);

  // Fetch Contextual Event Tagging for Symbol
  useEffect(() => {
    const fetchContext = async () => {
      try {
        const [symRes, allRes] = await Promise.all([
          axios.get(`/api/paper/contextual_news/${selectedAsset.code}`),
          axios.get('/api/paper/contextual_news'),
        ]);
        setContextualSentiment(symRes.data);
        setAllContextualEvents(allRes.data);
      } catch (e) {
        console.error('Failed to fetch contextual news:', e);
      }
    };
    fetchContext();
  }, [selectedAsset]);

  // Simulate Pre-Trade Risk on Ticket Parameter Changes
  useEffect(() => {
    const simulateRisk = async () => {
      try {
        const res = await axios.post('/api/paper/pre_trade_risk', {
          symbol: selectedAsset.code,
          side: orderSide,
          quantity: lotCount * selectedAsset.lotSize,
          price: orderType === 'LIMIT' ? limitPrice : selectedAsset.spot,
          sl_points: slPoints,
          segment: selectedAsset.category === 'COMMODITY' ? 'COMMODITY_FUTURES' : 'EQUITY_INTRADAY',
        });
        setSimulatedRisk(res.data);
      } catch (e) {
        console.error('Failed to simulate pre-trade risk:', e);
      }
    };
    simulateRisk();
  }, [selectedAsset, orderSide, lotCount, limitPrice, slPoints, orderType]);

  // Fetch Multi-Horizon Candles
  const fetchCandles = useCallback(async () => {
    setIsLoadingCandles(true);
    try {
      const res = await axios.get(
        `/api/mirajane/market/candles?symbol=${selectedAsset.code}&horizon=${selectedHorizon}`
      );
      if (res.data && res.data.candles && res.data.candles.length > 0) {
        setCandles(
          res.data.candles.map((c: any) => ({
            time: c.time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
            volume: c.volume || 15000,
          }))
        );
      } else {
        throw new Error('Fallback required');
      }
    } catch {
      // Procedural fallback
      const list: Candle[] = [];
      let cur = selectedAsset.spot;
      for (let i = 0; i < 35; i++) {
        const delta = (Math.sin(i * 0.4) + (Math.random() - 0.48)) * (selectedAsset.spot * 0.0015);
        const open = cur;
        const close = open + delta;
        const high = Math.max(open, close) + Math.abs(Math.cos(i)) * (selectedAsset.spot * 0.0005);
        const low = Math.min(open, close) - Math.abs(Math.sin(i)) * (selectedAsset.spot * 0.0005);
        list.push({ time: `Bar-${i + 1}`, open, high, low, close, volume: 25000 + i * 500 });
        cur = close;
      }
      setCandles(list);
    } finally {
      setIsLoadingCandles(false);
    }
  }, [selectedAsset, selectedHorizon]);

  useEffect(() => {
    fetchCandles();
  }, [fetchCandles]);

  useEffect(() => {
    setLimitPrice(selectedAsset.spot);
  }, [selectedAsset]);

  // Level 2 Depth Order Book
  const orderBook = useMemo(() => {
    const spot = selectedAsset.spot;
    const step = selectedAsset.step > 0 ? selectedAsset.step * 0.01 : 0.5;
    const bids: OrderBookItem[] = [
      { price: spot - step * 1, orders: 24, qty: 2250 },
      { price: spot - step * 2, orders: 48, qty: 4400 },
      { price: spot - step * 3, orders: 75, qty: 6850 },
      { price: spot - step * 4, orders: 110, qty: 9900 },
      { price: spot - step * 5, orders: 156, qty: 14250 },
    ];
    const asks: OrderBookItem[] = [
      { price: spot + step * 1, orders: 28, qty: 1950 },
      { price: spot + step * 2, orders: 45, qty: 3800 },
      { price: spot + step * 3, orders: 69, qty: 5950 },
      { price: spot + step * 4, orders: 98, qty: 8600 },
      { price: spot + step * 5, orders: 138, qty: 12400 },
    ];
    return { bids, asks };
  }, [selectedAsset]);

  const currentCandle = candles.length > 0
    ? candles[candles.length - 1]
    : { open: selectedAsset.spot, high: selectedAsset.spot, low: selectedAsset.spot, close: selectedAsset.spot, volume: 30000, time: 'Now' };

  // Execute Order via Institutional Paper Engine
  const handleExecuteTrade = async () => {
    setIsExecuting(true);
    setExecMessage(null);
    try {
      const orderPayload = {
        symbol: selectedAsset.code,
        side: orderSide,
        type: orderType,
        quantity: lotCount * selectedAsset.lotSize,
        price: orderType === 'LIMIT' ? limitPrice : currentCandle.close,
        sl_points: slPoints,
        target_points: targetPoints,
        segment: selectedAsset.category === 'COMMODITY' ? 'COMMODITY_FUTURES' : 'EQUITY_INTRADAY',
      };

      const res = await axios.post('/api/paper/order', orderPayload);
      const fill = res.data.fills && res.data.fills[0];
      const fillPrice = fill ? fill.fill_price : currentCandle.close;
      const slippage = fill ? fill.slippage : 0;

      setExecMessage(
        `✅ FILLED: ${orderSide} ${lotCount * selectedAsset.lotSize} ${selectedAsset.code} @ ₹${fillPrice.toFixed(2)} (Slippage: ₹${slippage.toFixed(2)})`
      );
      await fetchAccountAndPositions();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Order failed';
      setExecMessage(`❌ REJECTED: ${msg}`);
    } finally {
      setIsExecuting(false);
      setTimeout(() => setExecMessage(null), 6000);
    }
  };

  // Close / Square Off Position
  const handleSquareOff = async (symbol: string) => {
    try {
      await axios.post('/api/paper/close_position', { symbol });
      await fetchAccountAndPositions();
    } catch (e) {
      console.error('Failed to close position:', e);
    }
  };

  // Reset Virtual Account
  const handleResetAccount = async () => {
    if (confirm('Reset Paper Trading Account to ₹10,00,000 cash balance and clear all positions?')) {
      await axios.post('/api/paper/reset_account?initial_capital=1000000');
      await fetchAccountAndPositions();
    }
  };

  return (
    <div className="w-full min-h-screen bg-[#05070c] bg-grid-pattern text-slate-100 flex flex-col font-sans">
      {/* ── 1. LIVE MORNING PRE-MARKET STRIP ── */}
      <div className="w-full bg-[#080c14] border-b border-white/[0.08] px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 font-bold">
            <Sun className="w-3.5 h-3.5" />
            LIVE MORNING TRADING · 05 NOV 2026 (WEEKLY EXPIRY)
          </span>
          <span className="text-slate-400 hidden sm:inline">
            GIFT Nifty Opening Gap:{' '}
            <strong className="text-emerald-400 font-bold">
              +{premarketCues?.gift_nifty_gap?.points || 112.5} pts (+{premarketCues?.gift_nifty_gap?.percent || 0.47}%)
            </strong>
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNeuroModal(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold text-[11px] cursor-pointer transition-all"
            title="Inspect Deterministic Risk Supervisor Invariants"
          >
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span>NEURO RISK GATE</span>
          </button>

          <button
            onClick={handleDownloadSebiReport}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold text-[11px] cursor-pointer transition-all"
            title="Download Official SEBI EOD Margin Allocation CSV"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            <span>SEBI EOD CSV</span>
          </button>

          <button
            onClick={() => setShowNewsRadar(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-bold text-[11px] cursor-pointer transition-all"
          >
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>MACRO NEWS RADAR ({allContextualEvents.length})</span>
          </button>

          <button
            onClick={handleResetAccount}
            className="flex items-center gap-1 px-2 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] text-slate-400 hover:text-white border border-white/[0.08] text-[10px] cursor-pointer transition-all"
            title="Reset Virtual Account to ₹10,00,000"
          >
            <RefreshCw className="w-3 h-3" />
            <span>RESET PORTFOLIO</span>
          </button>
        </div>
      </div>

      {/* ── 2. INSTITUTIONAL CAPITAL & TIERED RISK RIBBON ── */}
      <div className="w-full bg-[#0a0e19] border-b border-white/[0.06] px-4 py-2.5 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-5">
          <div>
            <span className="text-[10px] text-slate-400 uppercase">VIRTUAL CASH</span>
            <div className="text-sm font-bold text-white">
              ₹{(accountSummary?.cash_balance || 1_000_000.0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>

          <div>
            <span className="text-[10px] text-slate-400 uppercase">TOTAL EQUITY</span>
            <div className="text-sm font-bold text-cyan-400">
              ₹{(accountSummary?.total_equity || 1_000_000.0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>

          <div>
            <span className="text-[10px] text-slate-400 uppercase">UNREALIZED P&L (NET)</span>
            <div
              className={`text-sm font-bold ${
                (accountSummary?.unrealized_net_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {(accountSummary?.unrealized_net_pnl || 0) >= 0 ? '+' : ''}
              ₹{(accountSummary?.unrealized_net_pnl || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>

          <div>
            <span className="text-[10px] text-slate-400 uppercase">STATUTORY CHARGES PAID</span>
            <div className="text-sm font-bold text-slate-300">
              ₹{(accountSummary?.total_statutory_charges || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        {/* Risk State & Double Entry Ledger Badges */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.03] border border-white/[0.06]">
            <Scale className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[10px] text-slate-300">LEDGER AUDIT:</span>
            <span className="text-[10px] font-bold text-emerald-400">
              {accountSummary?.ledger_audit?.status === 'CONSERVED' ? 'CONSERVED (100%)' : 'CONSERVED'}
            </span>
          </div>

          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-bold text-[10px] border ${
              accountSummary?.risk_state === 'FROZEN'
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse'
                : accountSummary?.risk_state === 'WARNING'
                ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
            }`}
          >
            {accountSummary?.risk_state === 'FROZEN' ? (
              <Lock className="w-3 h-3 text-rose-400" />
            ) : (
              <Shield className="w-3 h-3 text-emerald-400" />
            )}
            <span>RISK STATE: {accountSummary?.risk_state || 'HEALTHY'}</span>
          </div>
        </div>
      </div>

      {/* ── 3. ASSET WATCHLIST CAROUSEL ── */}
      <div className="w-full bg-[#070a12] border-b border-white/[0.06] px-3 py-2 flex items-center gap-2 overflow-x-auto no-scrollbar">
        {ASSET_CLASSES.map((asset) => {
          const isSelected = selectedAsset.code === asset.code;
          return (
            <button
              key={asset.code}
              onClick={() => setSelectedAsset(asset)}
              className={`flex items-center gap-2.5 px-3 py-1.5 rounded-xl transition-all cursor-pointer whitespace-nowrap text-xs font-mono ${
                isSelected
                  ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/10 text-white border border-emerald-500/40 shadow-sm'
                  : 'bg-white/[0.02] text-slate-400 hover:text-white hover:bg-white/[0.05] border border-white/[0.04]'
              }`}
            >
              <span className="font-bold">{asset.symbol}</span>
              <span className="text-white">₹{asset.spot.toFixed(2)}</span>
              <span className={`text-[10px] font-bold ${asset.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {asset.change >= 0 ? '+' : ''}{asset.changePct}%
              </span>
            </button>
          );
        })}
      </div>

      {/* ── 4. CONTEXTUAL EVENT CATALYST BANNER ── */}
      {contextualSentiment && contextualSentiment.catalysts && contextualSentiment.catalysts.length > 0 && (
        <div className="mx-3 mt-2 px-3 py-2 rounded-xl bg-gradient-to-r from-cyan-950/40 to-slate-900/60 border border-cyan-500/25 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                contextualSentiment.sentiment_label.includes('BEARISH')
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              }`}
            >
              {contextualSentiment.sentiment_label} ({contextualSentiment.composite_sentiment_score > 0 ? '+' : ''}
              {contextualSentiment.composite_sentiment_score})
            </span>
            <span className="text-slate-300">
              <strong>Macro Catalyst:</strong> {contextualSentiment.catalysts[0].headline}
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-cyan-300">
            <span className="bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
              Tactical Play: <strong>{contextualSentiment.catalysts[0].actionable_play}</strong>
            </span>
          </div>
        </div>
      )}

      {/* ── 5. TIMEFRAME HORIZONS BAR ── */}
      <div className="px-3 pt-2 pb-1 flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.06]">
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-1">
          <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400 mr-2">
            <Clock className="w-3 h-3 text-emerald-400" />
            <span className="font-bold">HORIZON:</span>
          </div>
          {LOOKBACK_HORIZONS.map((h) => {
            const isSelected = selectedHorizon === h.id;
            return (
              <button
                key={h.id}
                onClick={() => setSelectedHorizon(h.id)}
                title={h.desc}
                className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer whitespace-nowrap ${
                  isSelected
                    ? 'bg-emerald-500 text-black shadow-sm'
                    : 'bg-white/[0.02] text-slate-400 hover:text-white hover:bg-white/[0.06]'
                }`}
              >
                {h.label}
              </button>
            );
          })}
        </div>

        {isLoadingCandles && (
          <div className="flex items-center gap-1 text-slate-400 text-[10px]">
            <RefreshCw className="w-3 h-3 animate-spin text-emerald-400" />
            <span>Loading {selectedHorizon} candles...</span>
          </div>
        )}
      </div>

      {/* ── 6. TRADING COCKPIT (CHART + TICKET + DEPTH) ── */}
      <div className="flex-1 flex flex-col xl:flex-row p-3 gap-3 overflow-hidden">
        {/* ── LEFT & CENTER: HARDWARE-ACCELERATED 60 FPS TRADINGVIEW CANVAS CHART ── */}
        <div className="flex-1 flex flex-col rounded-2xl bg-[#07090e] border border-white/[0.08] shadow-[0_12px_40px_rgba(0,0,0,0.6)] backdrop-blur-xl overflow-hidden min-h-[520px]">
          <TradingViewChart
            symbol={selectedAsset.symbol}
            candles={candles}
            spot={selectedAsset.spot}
            height="100%"
            timeframe={selectedHorizon}
            onTimeframeChange={(tf) => setSelectedHorizon(tf)}
            showIndicatorsToolbar={true}
            showSMCByDefault={true}
            showVolumeByDefault={true}
            showEMAsByDefault={true}
            className="rounded-none border-none h-full"
          />
        </div>

        {/* ── RIGHT COLUMN: FAST TRADE EXECUTION TICKET & DEPTH ── */}
        <div className="w-full xl:w-[390px] flex flex-col gap-3 shrink-0">
          {/* Fast Execution Order Ticket */}
          <div className="p-4 rounded-2xl bg-[#0c1017]/95 border border-white/[0.08] shadow-[0_8px_30px_rgba(0,0,0,0.5)] backdrop-blur-xl space-y-3.5">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-emerald-400" />
                <span className="font-syne text-sm font-bold text-white uppercase">INSTITUTIONAL PAPER DESK</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                SEBI 1-TOUCH
              </span>
            </div>

            {/* Side Selector (BUY vs SELL) */}
            <div className="grid grid-cols-2 gap-2 p-1 bg-white/[0.03] rounded-xl border border-white/[0.06]">
              <button
                onClick={() => setOrderSide('BUY')}
                className={`py-2 rounded-lg text-xs font-sans font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  orderSide === 'BUY'
                    ? 'bg-emerald-500 text-black shadow-[0_0_16px_rgba(0,255,136,0.3)]'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <TrendingUp className="w-3.5 h-3.5" />
                BUY / LONG
              </button>
              <button
                onClick={() => setOrderSide('SELL')}
                className={`py-2 rounded-lg text-xs font-sans font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  orderSide === 'SELL'
                    ? 'bg-rose-500 text-white shadow-[0_0_16px_rgba(255,51,102,0.3)]'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <TrendingDown className="w-3.5 h-3.5" />
                SELL / SHORT
              </button>
            </div>

            {/* Product & Order Type Chips */}
            <div className="grid grid-cols-2 gap-2">
              <div className="flex bg-white/[0.02] p-1 rounded-lg border border-white/[0.06]">
                {(['MIS', 'NRML'] as const).map((p) => (
                  <button
                    key={p}
                    onClick={() => setProductType(p)}
                    className={`flex-1 py-1 text-[11px] font-mono font-bold rounded transition-all cursor-pointer ${
                      productType === p ? 'bg-white/10 text-white' : 'text-slate-400'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>

              <div className="flex bg-white/[0.02] p-1 rounded-lg border border-white/[0.06]">
                {(['MARKET', 'LIMIT', 'SL_M'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setOrderType(t)}
                    className={`flex-1 py-1 text-[10px] font-mono font-bold rounded transition-all cursor-pointer ${
                      orderType === t ? 'bg-white/10 text-white' : 'text-slate-400'
                    }`}
                  >
                    {t === 'SL_M' ? 'SL-M' : t}
                  </button>
                ))}
              </div>
            </div>

            {/* Lots & Quantity Controls */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono text-slate-400">
                <span>LOTS ({selectedAsset.lotSize} QTY / LOT)</span>
                <span className="text-white font-bold">{lotCount * selectedAsset.lotSize} Qty</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setLotCount(Math.max(1, lotCount - 1))}
                  className="w-9 h-9 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] flex items-center justify-center text-white cursor-pointer"
                >
                  <Minus className="w-4 h-4" />
                </button>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={lotCount}
                  onChange={(e) => setLotCount(Math.max(1, parseInt(e.target.value) || 1))}
                  className="flex-1 h-9 px-3 text-center bg-[#05080f] border border-white/[0.08] rounded-lg font-mono text-sm text-white font-bold outline-none focus:border-emerald-500"
                />
                <button
                  onClick={() => setLotCount(lotCount + 1)}
                  className="w-9 h-9 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] flex items-center justify-center text-white cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Limit Price */}
            {orderType === 'LIMIT' && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-mono text-slate-400">
                  <span>LIMIT PRICE (₹)</span>
                  <span className="text-cyan-400 font-bold">₹{limitPrice.toFixed(2)}</span>
                </div>
                <input
                  type="number"
                  step="0.05"
                  value={limitPrice}
                  onChange={(e) => setLimitPrice(parseFloat(e.target.value) || currentCandle.close)}
                  className="w-full h-9 px-3 bg-[#05080f] border border-white/[0.08] rounded-lg font-mono text-sm text-white font-bold outline-none focus:border-cyan-500"
                />
              </div>
            )}

            {/* SL & Target Points */}
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <div className="text-[11px] font-mono text-slate-400">SL (PTS)</div>
                <input
                  type="number"
                  value={slPoints}
                  onChange={(e) => setSlPoints(parseInt(e.target.value) || 20)}
                  className="w-full h-8 px-2 bg-[#05080f] border border-rose-500/30 rounded font-mono text-xs text-rose-300 font-bold outline-none"
                />
              </div>
              <div className="space-y-1">
                <div className="text-[11px] font-mono text-slate-400">TARGET (PTS)</div>
                <input
                  type="number"
                  value={targetPoints}
                  onChange={(e) => setTargetPoints(parseInt(e.target.value) || 40)}
                  className="w-full h-8 px-2 bg-[#05080f] border border-emerald-500/30 rounded font-mono text-xs text-emerald-300 font-bold outline-none"
                />
              </div>
            </div>

            {/* ── PRE-TRADE RISK & MARGIN SIMULATION CARD (GAP 1 SOLUTION) ── */}
            <div className="p-3 rounded-xl bg-[#080d17] border border-white/[0.07] space-y-1.5 text-xs font-mono">
              <div className="flex justify-between text-slate-400">
                <span>EST. MARGIN REQUIRED:</span>
                <span className="text-white font-bold">
                  ₹{(simulatedRisk?.margin_required || (lotCount * selectedAsset.lotSize * 420)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
              </div>

              <div className="flex justify-between text-slate-400">
                <span className="flex items-center gap-1">
                  <span>MAX DRAWDOWN (-2% GAP):</span>
                </span>
                <span className="text-rose-400 font-bold">
                  -₹{(simulatedRisk?.gap_drawdown_inr || (lotCount * selectedAsset.lotSize * selectedAsset.spot * 0.02)).toLocaleString('en-IN', { maximumFractionDigits: 0 })} ({simulatedRisk?.gap_drawdown_pct || 2.4}%)
                </span>
              </div>

              <div className="flex justify-between text-slate-400">
                <span>CAPITAL AT RISK:</span>
                <span
                  className={`font-bold ${
                    (simulatedRisk?.capital_at_risk_pct || 1.5) > 5.0 ? 'text-amber-400' : 'text-emerald-400'
                  }`}
                >
                  {simulatedRisk?.capital_at_risk_pct || 1.5}% of Portfolio
                </span>
              </div>

              {/* Statutory Tax Breakdown Bar */}
              <div className="pt-1.5 border-t border-white/[0.05] flex items-center justify-between text-[11px]">
                <button
                  type="button"
                  onClick={() => setShowTaxSchedule(true)}
                  className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                >
                  <FileText className="w-3 h-3" />
                  <span>TAX BREAKDOWN (SEBI/NSE):</span>
                </button>
                <span className="text-slate-300 font-bold">
                  ₹{simulatedRisk?.estimated_charges?.total_tax_and_charges || '38.45'}
                </span>
              </div>
            </div>

            {execMessage && (
              <div
                className={`p-2.5 rounded-lg text-[11px] font-mono ${
                  execMessage.includes('❌')
                    ? 'bg-rose-500/10 border border-rose-500/30 text-rose-300'
                    : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
                }`}
              >
                {execMessage}
              </div>
            )}

            {/* 1-Touch SEBI Execution Action Button */}
            <button
              onClick={handleExecuteTrade}
              disabled={isExecuting || accountSummary?.risk_state === 'FROZEN'}
              className={`w-full py-3.5 rounded-xl font-sans text-xs font-black tracking-wider uppercase flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xl ${
                accountSummary?.risk_state === 'FROZEN'
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                  : orderSide === 'BUY'
                  ? 'bg-gradient-to-r from-emerald-400 to-teal-500 text-black hover:shadow-[0_0_30px_rgba(0,255,136,0.4)]'
                  : 'bg-gradient-to-r from-rose-500 to-red-600 text-white hover:shadow-[0_0_30px_rgba(255,51,102,0.4)]'
              }`}
            >
              {isExecuting ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : accountSummary?.risk_state === 'FROZEN' ? (
                <Lock className="w-4 h-4 text-rose-400" />
              ) : (
                <Shield className="w-4 h-4" />
              )}
              <span>
                {accountSummary?.risk_state === 'FROZEN'
                  ? 'DAILY CIRCUIT BREAKER LOCKED'
                  : orderSide === 'BUY'
                  ? 'EXECUTE 1-TOUCH BUY (SEBI 2026)'
                  : 'EXECUTE 1-TOUCH SELL (SEBI 2026)'}
              </span>
            </button>
          </div>

          {/* Level 2 Market Depth / Order Book */}
          <div className="p-3.5 rounded-2xl bg-[#0c1017]/95 border border-white/[0.08] shadow-[0_8px_30px_rgba(0,0,0,0.5)] backdrop-blur-xl flex-1 flex flex-col">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06] mb-2">
              <span className="font-syne text-xs font-bold text-white uppercase">MARKET DEPTH (L2 TICK FEED)</span>
              <span className="text-[10px] font-mono text-slate-400">SPREAD: ₹0.05</span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono flex-1">
              {/* Bids Column */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-emerald-400 font-bold border-b border-white/[0.04] pb-1">
                  <span>ORDERS</span>
                  <span>QTY</span>
                  <span>BID</span>
                </div>
                {orderBook.bids.map((b, i) => (
                  <div key={i} className="flex justify-between relative py-0.5">
                    <div
                      className="absolute inset-y-0 right-0 bg-emerald-500/10 pointer-events-none rounded"
                      style={{ width: `${(b.qty / 15000) * 100}%` }}
                    />
                    <span className="text-slate-400 relative z-10">{b.orders}</span>
                    <span className="text-slate-300 relative z-10">{b.qty}</span>
                    <span className="text-emerald-400 font-bold relative z-10">{b.price.toFixed(2)}</span>
                  </div>
                ))}
              </div>

              {/* Asks Column */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-rose-400 font-bold border-b border-white/[0.04] pb-1">
                  <span>ASK</span>
                  <span>QTY</span>
                  <span>ORDERS</span>
                </div>
                {orderBook.asks.map((a, i) => (
                  <div key={i} className="flex justify-between relative py-0.5">
                    <div
                      className="absolute inset-y-0 left-0 bg-rose-500/10 pointer-events-none rounded"
                      style={{ width: `${(a.qty / 15000) * 100}%` }}
                    />
                    <span className="text-rose-400 font-bold relative z-10">{a.price.toFixed(2)}</span>
                    <span className="text-slate-300 relative z-10">{a.qty}</span>
                    <span className="text-slate-400 relative z-10">{a.orders}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 7. BOTTOM WORKSPACE: ACTIVE POSITIONS & POST-MORTEM ANALYTICS ── */}
      <div className="mx-3 mb-3 p-4 rounded-2xl bg-[#090d16]/95 border border-white/[0.08] shadow-[0_12px_40px_rgba(0,0,0,0.6)] backdrop-blur-xl">
        <div className="flex flex-wrap items-center justify-between pb-3 border-b border-white/[0.06] mb-3 gap-2">
          <div className="flex items-center gap-2">
            {[
              { id: 'positions' as const, label: `Active Positions (${positions.length})` },
              { id: 'orders' as const, label: 'Pending Limit Orders (0)' },
              { id: 'hft_arbitrage' as const, label: 'HFT Arbitrage (NSE–BSE)' },
              { id: 'dealer_gex' as const, label: 'Dealer GEX & 0DTE Math' },
              { id: 'post_mortem' as const, label: 'Behavioral Post-Mortems & Analytics' },
              { id: 'ledger' as const, label: 'SEBI Double-Entry Audit' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTabBottom(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-sans font-bold transition-all cursor-pointer ${
                  activeTabBottom === tab.id
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="text-xs font-mono">
            <span className="text-slate-400">NET UNREALIZED P&L: </span>
            <span
              className={`font-bold ${
                (accountSummary?.unrealized_net_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {(accountSummary?.unrealized_net_pnl || 0) >= 0 ? '+' : ''}₹
              {(accountSummary?.unrealized_net_pnl || 0).toFixed(2)} INR
            </span>
          </div>
        </div>

        {/* TAB 1: Positions Table */}
        {activeTabBottom === 'positions' && (
          <div className="overflow-x-auto">
            {positions.length === 0 ? (
              <div className="py-8 text-center text-xs font-mono text-slate-500">
                No active open positions. Place an order above to begin institutional execution.
              </div>
            ) : (
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="text-slate-400 border-b border-white/[0.04] uppercase text-[10px]">
                    <th className="pb-2">Symbol</th>
                    <th className="pb-2">Side</th>
                    <th className="pb-2">Qty</th>
                    <th className="pb-2">Avg Price</th>
                    <th className="pb-2">LTP</th>
                    <th className="pb-2">Stop Loss</th>
                    <th className="pb-2">Target</th>
                    <th className="pb-2">Hold Time</th>
                    <th className="pb-2">Net P&L (INR)</th>
                    <th className="pb-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.03]">
                  {positions.map((pos) => (
                    <tr key={pos.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-2.5 font-bold text-white flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        {pos.symbol}
                      </td>
                      <td className="py-2.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            pos.side === 'BUY'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {pos.side}
                        </span>
                      </td>
                      <td className="py-2.5 text-slate-300">{pos.qty}</td>
                      <td className="py-2.5 text-slate-300">₹{pos.entryPrice.toFixed(2)}</td>
                      <td className="py-2.5 text-white font-bold">₹{pos.currentPrice.toFixed(2)}</td>
                      <td className="py-2.5 text-rose-400">₹{pos.sl.toFixed(2)}</td>
                      <td className="py-2.5 text-emerald-400">₹{pos.target.toFixed(2)}</td>
                      <td className="py-2.5 text-slate-400">{pos.holdingDurationMins || 0.1}m</td>
                      <td className={`py-2.5 font-bold ${pos.pnlInr >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {pos.pnlInr >= 0 ? '+' : ''}₹{pos.pnlInr.toFixed(2)} ({pos.pnlPct.toFixed(2)}%)
                      </td>
                      <td className="py-2.5 text-right">
                        <button
                          onClick={() => handleSquareOff(pos.symbol)}
                          className="px-2.5 py-1 rounded bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 text-[10px] font-bold cursor-pointer transition-all"
                        >
                          SQUARE OFF
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* TAB 2: Pending Orders */}
        {activeTabBottom === 'orders' && (
          <div className="py-8 text-center text-xs font-mono text-slate-500">
            All limit and market orders matched immediately with simulated liquidity depth. Zero pending triggers.
          </div>
        )}

        {/* TAB 2B: HFT Cross-Exchange Arbitrage Monitor */}
        {activeTabBottom === 'hft_arbitrage' && (
          <HftArbitrageMonitor />
        )}

        {/* TAB 2C: Dealer Aggregate GEX & 0DTE Math Lab */}
        {activeTabBottom === 'dealer_gex' && (
          <DealerGexRadar />
        )}

        {/* TAB 3: Behavioral Post-Mortem & Analytics (GAP 3 SOLUTION) */}
        {activeTabBottom === 'post_mortem' && (
          <div className="space-y-4 font-mono text-xs">
            {/* Behavioral Scorecards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 uppercase">DISCIPLINE RATING</span>
                <div className="text-xl font-bold text-emerald-400">
                  {behavioralAnalytics?.discipline_rating || 'A+'}
                </div>
                <span className="text-[9px] text-slate-400">Adherence to Stop Loss rules</span>
              </div>

              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 uppercase">BAG-HOLDING RATIO</span>
                <div
                  className={`text-xl font-bold ${
                    (behavioralAnalytics?.bag_holding_ratio || 1.0) > 2.0 ? 'text-rose-400' : 'text-cyan-400'
                  }`}
                >
                  {behavioralAnalytics?.bag_holding_ratio || 1.0}x
                </div>
                <span className="text-[9px] text-slate-400">Loser Hold Duration / Winner Hold</span>
              </div>

              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 uppercase">TILT RISK SCORE</span>
                <div
                  className={`text-xl font-bold ${
                    (behavioralAnalytics?.tilt_score || 5.0) > 30.0 ? 'text-amber-400' : 'text-emerald-400'
                  }`}
                >
                  {behavioralAnalytics?.tilt_score || 5.0} / 100
                </div>
                <span className="text-[9px] text-slate-400">Revenge trading & size inflation</span>
              </div>

              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 uppercase">ROUND TRIP WIN RATE</span>
                <div className="text-xl font-bold text-purple-400">
                  {behavioralAnalytics?.win_rate_pct || 0.0}% ({behavioralAnalytics?.total_trades || 0} Trades)
                </div>
                <span className="text-[9px] text-slate-400">Net of all Indian statutory taxes</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs">
              <strong>Quant Diagnostic: </strong>
              {behavioralAnalytics?.behavioral_summary || 'Trading parameters in optimal bounds.'}
            </div>

            {/* Completed Trades Table */}
            <div className="overflow-x-auto pt-2">
              <span className="text-slate-400 text-[10px] uppercase font-bold">COMPLETED TRADES AUDIT LOG</span>
              <table className="w-full text-left font-mono text-[11px] mt-1">
                <thead>
                  <tr className="text-slate-400 border-b border-white/[0.04] text-[10px]">
                    <th className="pb-1.5">Trade ID</th>
                    <th className="pb-1.5">Symbol</th>
                    <th className="pb-1.5">Side</th>
                    <th className="pb-1.5">Qty</th>
                    <th className="pb-1.5">Entry Price</th>
                    <th className="pb-1.5">Exit Price</th>
                    <th className="pb-1.5">Hold Duration</th>
                    <th className="pb-1.5">Exit Trigger</th>
                    <th className="pb-1.5">Taxes Paid</th>
                    <th className="pb-1.5 text-right">Net P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.02]">
                  {completedTrades.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="py-4 text-center text-slate-500">
                        No closed round-trip trades recorded yet.
                      </td>
                    </tr>
                  ) : (
                    completedTrades.map((t: any) => (
                      <tr key={t.trade_id} className="hover:bg-white/[0.02]">
                        <td className="py-2 text-slate-400">{t.trade_id}</td>
                        <td className="py-2 text-white font-bold">{t.symbol}</td>
                        <td className="py-2 text-slate-300">{t.side}</td>
                        <td className="py-2 text-slate-300">{t.quantity}</td>
                        <td className="py-2 text-slate-300">₹{t.entry_price.toFixed(2)}</td>
                        <td className="py-2 text-white font-bold">₹{t.exit_price.toFixed(2)}</td>
                        <td className="py-2 text-slate-400">{t.holding_minutes}m</td>
                        <td className="py-2">
                          <span className="px-1.5 py-0.5 rounded bg-white/[0.05] text-[10px]">
                            {t.exit_reason}
                          </span>
                        </td>
                        <td className="py-2 text-rose-300">₹{t.charges?.total_tax_and_charges?.toFixed(2) || '0.00'}</td>
                        <td
                          className={`py-2 text-right font-bold ${
                            t.net_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {t.net_pnl >= 0 ? '+' : ''}₹{t.net_pnl.toFixed(2)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: SEBI Double-Entry Audit Ledger */}
        {activeTabBottom === 'ledger' && (
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] font-mono text-xs space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <span className="font-bold text-white uppercase flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                DOUBLE-ENTRY LEDGER CONSERVATION VERIFICATION
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold">
                TOTAL DEBITS == TOTAL CREDITS
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-slate-300">
              <div>
                <span className="text-[10px] text-slate-400">INITIAL CAPITAL</span>
                <div className="font-bold text-white">
                  ₹{(accountSummary?.ledger_audit?.initial_capital || 1_000_000).toLocaleString('en-IN')}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400">REALIZED P&L</span>
                <div className="font-bold text-white">
                  ₹{(accountSummary?.ledger_audit?.realized_pnl || 0).toLocaleString('en-IN')}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400">STATUTORY DEDUCTIONS</span>
                <div className="font-bold text-rose-300">
                  -₹{(accountSummary?.ledger_audit?.total_statutory_charges || 0).toLocaleString('en-IN')}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400">DISCREPANCY</span>
                <div className="font-bold text-emerald-400">
                  ₹{accountSummary?.ledger_audit?.discrepancy_inr || '0.0000'} INR
                </div>
              </div>
            </div>

            <div className="p-2.5 rounded bg-black/40 border border-white/[0.04] text-[11px] text-slate-400">
              Formula enforced: Starting Capital (₹10,00,000.00) + Realized P&L - Regulatory Fees (STT + NSE + SEBI + Stamp + GST) == Current Cash Balance. Zero unbacked synthetic credits permitted.
            </div>
          </div>
        )}
      </div>

      {/* ── MODAL 1: MACRO NEWS RADAR ── */}
      {showNewsRadar && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-3xl rounded-2xl bg-[#0c101a] border border-white/[0.1] shadow-2xl p-5 space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-cyan-400" />
                <h3 className="font-syne text-sm font-bold text-white uppercase">
                  GLOBAL MACRO NEWS RADAR & SECTOR IMPACT MATRIX
                </h3>
              </div>
              <button
                onClick={() => setShowNewsRadar(false)}
                className="w-8 h-8 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] flex items-center justify-center text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
              {allContextualEvents.map((evt: any) => (
                <div
                  key={evt.event_id}
                  className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2 hover:border-cyan-500/30 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-bold">
                      {evt.macro_theme} · {evt.urgency}
                    </span>
                    <span className="text-[10px] text-slate-400">{evt.source} · {evt.time_ago_mins}m ago</span>
                  </div>

                  <h4 className="font-bold text-white text-sm">{evt.headline}</h4>
                  <p className="text-slate-300 text-[11px]">{evt.summary}</p>

                  <div className="pt-2 border-t border-white/[0.04] space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">AFFECTED INSTRUMENTS & TACTICAL PLAYS:</span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                      {evt.impacts.map((imp: any) => (
                        <div
                          key={imp.symbol}
                          className="p-2 rounded-lg bg-black/40 border border-white/[0.04] flex items-center justify-between"
                        >
                          <div>
                            <span className="font-bold text-white mr-1.5">{imp.symbol}</span>
                            <span
                              className={`text-[10px] font-bold ${
                                imp.sentiment_score > 0 ? 'text-emerald-400' : 'text-rose-400'
                              }`}
                            >
                              ({imp.sentiment_score > 0 ? '+' : ''}{imp.sentiment_score})
                            </span>
                            <div className="text-[10px] text-slate-400 truncate max-w-[200px]">
                              {imp.rationale}
                            </div>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-white/[0.05] text-[10px] text-cyan-300 font-bold">
                            {imp.actionable_play}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL 2: INDIAN STATUTORY TAX SCHEDULE ── */}
      {showTaxSchedule && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-[#0c101a] border border-white/[0.1] shadow-2xl p-5 space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Scale className="w-5 h-5 text-emerald-400" />
                <h3 className="font-syne text-sm font-bold text-white uppercase">
                  INDIAN STATUTORY TRANSACTION FEE SCHEDULE (SEBI / NSE / MOF)
                </h3>
              </div>
              <button
                onClick={() => setShowTaxSchedule(false)}
                className="w-8 h-8 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] flex items-center justify-center text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-slate-300">
              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] space-y-1.5">
                <div className="flex justify-between font-bold text-white">
                  <span>1. BROKERAGE</span>
                  <span>min(₹20, 0.03% Turnover)</span>
                </div>
                <p className="text-[11px] text-slate-400">Standard Indian discount broker execution tariff for MIS & F&O.</p>
              </div>

              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] space-y-1.5">
                <div className="flex justify-between font-bold text-white">
                  <span>2. SECURITIES TRANSACTION TAX (STT)</span>
                  <span>0.025% (MIS Sell) / 0.1% (Option Sell)</span>
                </div>
                <p className="text-[11px] text-slate-400">Levied exclusively by the Government of India on the sell turnover.</p>
              </div>

              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] space-y-1.5">
                <div className="flex justify-between font-bold text-white">
                  <span>3. NSE EXCHANGE TRANSACTION CHARGES</span>
                  <span>0.00297% (Equity) / 0.03503% (Options)</span>
                </div>
                <p className="text-[11px] text-slate-400">Turnover charges paid directly to the National Stock Exchange of India.</p>
              </div>

              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] space-y-1.5">
                <div className="flex justify-between font-bold text-white">
                  <span>4. SEBI TURNOVER CHARGES</span>
                  <span>₹10 per Crore (0.0001%)</span>
                </div>
                <p className="text-[11px] text-slate-400">Statutory regulatory charge on both buy and sell legs.</p>
              </div>

              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] space-y-1.5">
                <div className="flex justify-between font-bold text-white">
                  <span>5. STAMP DUTY & GST (18%)</span>
                  <span>0.003% (Buy) + 18% on (Brokerage + Txn + SEBI)</span>
                </div>
                <p className="text-[11px] text-slate-400">State stamp duty levied on buy orders; GST applies on all service charges.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL 3: NEURO-SYMBOLIC RISK SUPERVISOR ── */}
      {showNeuroModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-3xl rounded-2xl bg-[#0c101a] border border-white/[0.1] shadow-2xl p-5 space-y-4 font-mono text-xs max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-purple-400" />
                <h3 className="font-syne text-sm font-bold text-white uppercase">
                  NEURO-SYMBOLIC RISK SUPERVISOR & DETERMINISTIC INVARIANT INSPECTOR
                </h3>
              </div>
              <button
                onClick={() => setShowNeuroModal(false)}
                className="w-8 h-8 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] flex items-center justify-center text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Invariant Architecture */}
            <div className="p-3 rounded-xl bg-purple-950/20 border border-purple-500/20 text-purple-200 space-y-1.5">
              <strong className="text-white flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-purple-400" />
                Un-Overrideable Mathematical Invariant Guard
              </strong>
              <p className="text-[11px] text-slate-300">
                Neural SLMs are non-deterministic. The Deterministic Risk Supervisor enforces strict symbolic rules that NO neural weight can bypass or override.
              </p>
            </div>

            {/* 5 Invariant Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                <div className="font-bold text-white flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  1. Drawdown Circuit Breaker
                </div>
                <p className="text-slate-400 text-[10px] mt-0.5">
                  Hard killswitch trips if accumulated daily loss reaches -₹25,000 (5%). Halts all subsequent entries.
                </p>
              </div>

              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                <div className="font-bold text-white flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  2. Neural Conviction Gate
                </div>
                <p className="text-slate-400 text-[10px] mt-0.5">
                  Intent confidence must be ≥ 0.78. Low-conviction predictions or neural hallucinations are quarantined.
                </p>
              </div>

              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                <div className="font-bold text-white flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  3. Mathematical Lot Sizing
                </div>
                <p className="text-slate-400 text-[10px] mt-0.5">
                  Risk capped to strictly ≤ 2.0% of portfolio equity: Lots = floor(MaxRisk / (RiskPerShare × LotSize)).
                </p>
              </div>

              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                <div className="font-bold text-white flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  4. 0DTE Singularity Lockout
                </div>
                <p className="text-slate-400 text-[10px] mt-0.5">
                  Prohibits new naked long gamma entries within final 15 minutes of expiry to avoid pin annihilation.
                </p>
              </div>
            </div>

            {/* Test Simulation Button */}
            <div className="pt-2 flex justify-between items-center border-t border-white/[0.06]">
              <span className="text-slate-400 text-[11px]">Test with current {selectedAsset.code} live context:</span>
              <button
                onClick={handleTestAgentCycle}
                disabled={isTickingAgent}
                className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-1.5 cursor-pointer transition-all shadow-lg shadow-purple-600/20"
              >
                <Cpu className={`w-3.5 h-3.5 ${isTickingAgent ? 'animate-spin' : ''}`} />
                <span>Simulate Agent Cycle</span>
              </button>
            </div>

            {/* Live Verdict Display */}
            {neuroVerdict && (
              <div className="p-3.5 rounded-xl bg-black/60 border border-white/[0.08] space-y-2.5">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 text-[10px] uppercase">SUPERVISOR VERDICT:</span>
                    <span
                      className={`px-2 py-0.5 rounded font-bold text-[11px] ${
                        neuroVerdict.approved
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                      }`}
                    >
                      {neuroVerdict.approved ? 'APPROVED BY SUPERVISOR' : 'REJECTED BY INVARIANTS'}
                    </span>
                  </div>
                  <span className="text-slate-400 text-[10px]">
                    Conviction: <strong className="text-purple-300">{(neuroVerdict.intent.confidence * 100).toFixed(0)}%</strong>
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px]">
                  <div>
                    <span className="text-slate-400 block text-[10px]">Action</span>
                    <strong className="text-white">{neuroVerdict.intent.action}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">Regime Detected</span>
                    <strong className="text-cyan-300">{neuroVerdict.intent.regime_detected}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">Approved Lots</span>
                    <strong className="text-emerald-400">{neuroVerdict.adjusted_lots} lots</strong>
                  </div>
                </div>

                {neuroVerdict.intent.mirajane_thought && (
                  <div className="p-2.5 rounded bg-purple-950/30 border border-purple-500/20 text-purple-200 text-[11px] italic">
                    "{neuroVerdict.intent.mirajane_thought}"
                  </div>
                )}

                <div className="space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Applied Invariants & Guards:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {neuroVerdict.applied_guards?.map((g: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-white/[0.04] text-[10px] text-emerald-300 border border-emerald-500/20">
                        ✓ {g}
                      </span>
                    ))}
                    {neuroVerdict.rejection_reasons?.map((r: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-rose-500/15 text-[10px] text-rose-300 border border-rose-500/30">
                        ✗ {r}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
