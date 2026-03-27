import { useState } from 'react';
import { Play, Loader2, BarChart2 } from 'lucide-react';
import { EquityChart } from './EquityChart';

export function BacktestRunner() {
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [symbol, setSymbol] = useState("NIFTY50");
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-01-05");

  const runBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setRunning(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch('http://localhost:8000/backtest/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          symbol,
          start_date: startDate,
          end_date: endDate,
          model_id: "baseline_v1"
        })
      });

      if (!response.ok) {
        throw new Error("Failed to execute backtest");
      }

      const data = await response.json();
      setResults(data);

    } catch (err: any) {
      setError(err.message || "Unknown error occurred");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="glass-panel p-6 flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold bg-gradient-to-r from-ocean-100 to-ocean-300 bg-clip-text text-transparent flex items-center gap-2">
          <BarChart2 size={24} className="text-gold-500" />
          Strategy Simulator
        </h2>
        {results && (
          <div className="flex gap-4">
            <div className="text-right">
              <p className="text-xs text-ocean-400 font-mono">Total Return</p>
              <p className="font-bold text-green-400">+{results.metrics.total_return_pct}%</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-ocean-400 font-mono">Max Drawdown</p>
              <p className="font-bold text-red-400">-{results.metrics.max_drawdown_pct}%</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-ocean-400 font-mono">Sharpe</p>
              <p className="font-bold text-gold-400">{results.metrics.sharpe_ratio}</p>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={runBacktest} className="flex flex-wrap gap-4 items-end mb-6 bg-ocean-900/40 p-4 rounded-xl border border-ocean-800">
        <div className="flex flex-col gap-1 flex-1 min-w-[120px]">
          <label className="text-xs text-ocean-400 font-mono">Symbol</label>
          <input 
            value={symbol}
            onChange={e => setSymbol(e.target.value.toUpperCase())}
            className="bg-ocean-950 border border-ocean-700 rounded-lg px-3 py-2 text-ocean-100 focus:outline-none focus:border-gold-500 transition-colors"
          />
        </div>
        
        <div className="flex flex-col gap-1 flex-1 min-w-[140px]">
          <label className="text-xs text-ocean-400 font-mono">From</label>
          <input 
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
            className="bg-ocean-950 border border-ocean-700 rounded-lg px-3 py-2 text-ocean-100 focus:outline-none focus:border-gold-500 transition-colors cursor-pointer"
          />
        </div>

        <div className="flex flex-col gap-1 flex-1 min-w-[140px]">
          <label className="text-xs text-ocean-400 font-mono">To</label>
          <input 
            type="date"
            value={endDate}
            onChange={e => setEndDate(e.target.value)}
            className="bg-ocean-950 border border-ocean-700 rounded-lg px-3 py-2 text-ocean-100 focus:outline-none focus:border-gold-500 transition-colors cursor-pointer"
          />
        </div>

        <button 
          type="submit" 
          disabled={running}
          className="bg-gradient-to-br from-gold-500 to-gold-600 text-ocean-950 font-bold px-6 py-2 rounded-lg flex items-center justify-center gap-2 hover:to-gold-500 hover:shadow-[0_0_15px_rgba(245,158,11,0.4)] transition-all disabled:opacity-50 min-w-[140px]"
        >
          {running ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
          {running ? 'Simulating...' : 'Run Backtest'}
        </button>
      </form>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-3 rounded-lg mb-6 text-sm">
          {error}
        </div>
      )}

      <div className="flex-1 flex flex-col justify-end min-h-[300px]">
        <EquityChart data={results?.equity_curve || []} />
      </div>
    </div>
  );
}
