import { create } from 'zustand';

interface PortfolioState {
  globalNetLiquidity: number;
  activePositions: number;
  dailyPnl: number;
  sebiMarginUtilized: number;
  updatePortfolio: (updates: Partial<PortfolioState>) => void;
  resetMargin: () => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  globalNetLiquidity: 15200000.00, // INR 1.5 Cr Base Value
  activePositions: 12,
  dailyPnl: 142050.50,
  sebiMarginUtilized: 8500000.00,

  updatePortfolio: (updates) => set((state) => ({ ...state, ...updates })),
  resetMargin: () => set({ sebiMarginUtilized: 0 }),
}));
