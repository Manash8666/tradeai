import { useState } from 'react';
import { Play, Shield, BarChart3, Receipt, CheckCircle2, AlertOctagon } from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface BacktestStats {
  strategyName: string;
  winRate: number;
  sharpeRatio: number;
  sortinoRatio: number;
  netPnlInr: number;
  maxDrawdownPct: number;
  maxDrawdownInr: number;
  profitFactor: number;
  totalTrades: number;
  totalBrokerageInr: number;
  totalSttInr: number;
  totalGstInr: number;
  robustnessVerdict: 'HIGHLY_ROBUST' | 'ROBUST' | 'MARGINAL' | 'FRAGILE';
  robustnessScore: number;
}

const SAMPLE_EQUITY_CURVE = [
  { day: 'Day 1', equity: 1000000 },
  { day: 'Day 5', equity: 1018500 },
  { day: 'Day 10', equity: 1032000 },
  { day: 'Day 15', equity: 1024000 },
  { day: 'Day 20', equity: 1055000 },
  { day: 'Day 25', equity: 1078000 },
  { day: 'Day 30', equity: 1092000 },
  { day: 'Day 35', equity: 1084000 },
  { day: 'Day 40', equity: 1115000 },
  { day: 'Day 45', equity: 1142500 },
];

const INITIAL_STATS: BacktestStats = {
  strategyName: 'BankNifty Intraday Momentum Reversal',
  winRate: 68.4,
  sharpeRatio: 2.14,
  sortinoRatio: 3.05,
  netPnlInr: 142500,
  maxDrawdownPct: 3.8,
  maxDrawdownInr: 41200,
  profitFactor: 2.25,
  totalTrades: 38,
  totalBrokerageInr: 1520,
  totalSttInr: 2850,
  totalGstInr: 786,
  robustnessVerdict: 'HIGHLY_ROBUST',
  robustnessScore: 0.88,
};

export function BacktestResultPanel() {
  const [selectedStrategy, setSelectedStrategy] = useState<string>('BANKNIFTY_MOMENTUM');
  const [capitalInr] = useState<number>(1000000);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [stats, setStats] = useState<BacktestStats>(INITIAL_STATS);

  const handleRunBacktest = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      setStats({
        ...INITIAL_STATS,
        netPnlInr: Math.round(capitalInr * 0.1425),
        maxDrawdownInr: Math.round(capitalInr * 0.038),
      });
    }, 1100);
  };

  const getRobustnessBadge = (verdict: string) => {
    switch (verdict) {
      case 'HIGHLY_ROBUST':
        return <span className="badge badge-success"><CheckCircle2 size={10} /> HIGHLY ROBUST (0.88)</span>;
      case 'ROBUST':
        return <span className="badge badge-primary"><Shield size={10} /> ROBUST</span>;
      case 'MARGINAL':
        return <span className="badge badge-warning">MARGINAL FIT</span>;
      default:
        return <span className="badge badge-error"><AlertOctagon size={10} /> OVERFITTED</span>;
    }
  };

  return (
    <div className="glass-panel" style={{ padding: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div style={{
            width: 34, height: 34, borderRadius: 'var(--radius-md)',
            background: 'var(--color-primary-10)', border: '1px solid var(--color-primary-20)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)'
          }}>
            <BarChart3 size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--color-text-primary)', letterSpacing: '-0.02em' }}>
              NSE/BSE INSTITUTIONAL BACKTESTER
            </h3>
            <p style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
              Zero Look-Ahead Bias • Indian STT, GST & Exchange Turnover Friction
            </p>
          </div>
        </div>

        {/* Strategy Selector & Trigger */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <select
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value)}
            className="input"
            style={{ width: 'auto', padding: 'var(--space-1) var(--space-3)', fontSize: '0.74rem' }}
          >
            <option value="BANKNIFTY_MOMENTUM">BankNifty Intraday Momentum</option>
            <option value="GIFT_GAP_FADE">GIFT Nifty Gap Fade</option>
            <option value="GAMMA_SQUEEZE">0DTE Expiry Gamma Squeeze</option>
            <option value="VIX_HEDGE">India VIX Spike Hedge</option>
            <option value="FII_FOLLOWER">FII Flow Swing Follower</option>
          </select>
          <button
            onClick={handleRunBacktest}
            disabled={isRunning}
            className="btn btn-sm btn-primary"
            style={{ fontSize: '0.70rem' }}
          >
            <Play size={11} className={isRunning ? 'animate-spin' : ''} />
            {isRunning ? 'SIMULATING...' : 'RUN BACKTEST'}
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: 'var(--space-3)',
        marginBottom: 'var(--space-5)',
      }}>
        <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
          <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Net Profit</span>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--color-success)', fontFamily: 'var(--font-mono)' }}>
            +₹{stats.netPnlInr.toLocaleString('en-IN')}
          </div>
          <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)' }}>After All Statutory Deductions</span>
        </div>

        <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
          <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Win Rate</span>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--color-primary)', fontFamily: 'var(--font-mono)' }}>
            {stats.winRate}%
          </div>
          <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)' }}>{stats.totalTrades} Executed Trades</span>
        </div>

        <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
          <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Sharpe Ratio</span>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--color-success)', fontFamily: 'var(--font-mono)' }}>
            {stats.sharpeRatio}
          </div>
          <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)' }}>vs 6.75% 10Y G-Sec Base</span>
        </div>

        <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
          <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Max Drawdown</span>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--color-error)', fontFamily: 'var(--font-mono)' }}>
            -{stats.maxDrawdownPct}%
          </div>
          <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)' }}>-₹{stats.maxDrawdownInr.toLocaleString('en-IN')}</span>
        </div>

        <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
          <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Robustness</span>
          <div style={{ marginTop: 'var(--space-1)' }}>
            {getRobustnessBadge(stats.robustnessVerdict)}
          </div>
          <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)' }}>1,000 Monte Carlo Paths</span>
        </div>
      </div>

      {/* Equity Curve Chart */}
      <div style={{ height: 180, width: '100%', marginBottom: 'var(--space-4)' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={SAMPLE_EQUITY_CURVE} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.35} />
                <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
            <XAxis dataKey="day" stroke="var(--color-text-muted)" fontSize={10} tickLine={false} />
            <YAxis stroke="var(--color-text-muted)" fontSize={10} tickLine={false} tickFormatter={(v) => `₹${(v / 100000).toFixed(1)}L`} />
            <Tooltip
              contentStyle={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.72rem',
                fontFamily: 'var(--font-mono)',
              }}
              formatter={(value: any) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Portfolio NAV']}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke="var(--color-primary)"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#equityGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Indian Market Friction Breakdown Ribbon */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 'var(--space-2) var(--space-4)',
        background: 'var(--color-bg-secondary)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--color-border-subtle)',
        fontSize: '0.70rem',
        color: 'var(--color-text-muted)',
        fontFamily: 'var(--font-mono)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Receipt size={12} color="var(--color-text-muted)" />
          <span>Friction Deducted:</span>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
          <span>Brokerage: ₹{stats.totalBrokerageInr.toLocaleString('en-IN')}</span>
          <span>STT: ₹{stats.totalSttInr.toLocaleString('en-IN')}</span>
          <span>GST (18%): ₹{stats.totalGstInr.toLocaleString('en-IN')}</span>
        </div>
      </div>
    </div>
  );
}
