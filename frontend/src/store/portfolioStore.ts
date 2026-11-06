import { create } from 'zustand';

export interface MirajaneTrade {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  slPrice: number;
  targetPrice: number;
  strategyName: string;
  convictionScore: number;
  pnlInr: number;
  pnlPct: number;
  timestamp: number;
  active: boolean;
}

interface PortfolioState {
  globalNetLiquidity: number;
  activePositions: number;
  dailyPnl: number;
  sebiMarginUtilized: number;
  mirajaneTrades: MirajaneTrade[];
  addMirajaneTrade: (trade: MirajaneTrade) => void;
  closeMirajaneTrade: (idOrSymbol: string) => void;
  updateTradePrice: (symbol: string, currentPrice: number) => void;
  updatePortfolio: (updates: Partial<PortfolioState>) => void;
  resetMargin: () => void;
}

const loadStoredTrades = (): MirajaneTrade[] => {
  try {
    const raw = localStorage.getItem('mirajane_trades');
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch {
    // Ignore parse errors
  }
  return [];
};

const saveStoredTrades = (trades: MirajaneTrade[]) => {
  try {
    localStorage.setItem('mirajane_trades', JSON.stringify(trades));
  } catch {
    // Ignore storage errors
  }
};

export const usePortfolioStore = create<PortfolioState>((set) => ({
  globalNetLiquidity: 15200000.00, // INR 1.5 Cr Base Value
  activePositions: 12,
  dailyPnl: 142050.50,
  sebiMarginUtilized: 8500000.00,
  mirajaneTrades: loadStoredTrades(),

  addMirajaneTrade: (trade) =>
    set((state) => {
      // Replace or prepend trade
      const filtered = state.mirajaneTrades.filter((t) => t.id !== trade.id);
      const next = [trade, ...filtered];
      saveStoredTrades(next);
      return { mirajaneTrades: next, activePositions: state.activePositions + 1 };
    }),

  closeMirajaneTrade: (idOrSymbol) =>
    set((state) => {
      const next = state.mirajaneTrades.filter(
        (t) => t.id !== idOrSymbol && t.symbol !== idOrSymbol
      );
      saveStoredTrades(next);
      return { mirajaneTrades: next, activePositions: Math.max(0, state.activePositions - 1) };
    }),

  updateTradePrice: (symbol, currentPrice) =>
    set((state) => {
      const next = state.mirajaneTrades.map((t) => {
        if (t.symbol === symbol && t.active) {
          const mult = t.side === 'BUY' ? 1 : -1;
          const pnlInr = (currentPrice - t.entryPrice) * t.quantity * mult;
          const pnlPct = t.entryPrice > 0 ? ((currentPrice - t.entryPrice) / t.entryPrice) * 100 * mult : 0;
          return { ...t, currentPrice, pnlInr, pnlPct };
        }
        return t;
      });
      saveStoredTrades(next);
      return { mirajaneTrades: next };
    }),

  updatePortfolio: (updates) => set((state) => ({ ...state, ...updates })),
  resetMargin: () => set({ sebiMarginUtilized: 0 }),
}));
