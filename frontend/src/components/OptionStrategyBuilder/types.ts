export interface OptionGreek {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  iv: number;
}

export interface OptionChainStrike {
  strike: number;
  is_atm: boolean;
  call: {
    delta: number;
    ltp: number;
    oi: number;
    oi_pct: number;
    iv: number;
  };
  put: {
    delta: number;
    ltp: number;
    oi: number;
    oi_pct: number;
    iv: number;
  };
}

export interface ExpiryDate {
  label: string;
  date: string;
  days: number;
  dte_years: number;
}

export interface OptionChainData {
  symbol: string;
  name: string;
  spot: number;
  vix: number;
  fut: number;
  fut_expiry: string;
  lot_size: number;
  strike_step: number;
  atm_strike: number;
  expiries: ExpiryDate[];
  selected_expiry: ExpiryDate;
  strikes: OptionChainStrike[];
  timestamp_ist: string;
}

export interface StrategyLeg {
  id: string;
  action: 'BUY' | 'SELL';
  type: 'CE' | 'PE';
  strike: number;
  expiry: string;
  lots: number;
  quantity: number;
  price: number;
  iv: number;
  delta?: number;
  enabled?: boolean;
}

export interface ReadyMadeStrategy {
  id: string;
  name: string;
  category: 'Bullish' | 'Bearish' | 'Neutral' | 'Other';
  description: string;
  legs: {
    action: 'BUY' | 'SELL';
    type: 'CE' | 'PE';
    strike_offset: number;
    lots: number;
    expiry_idx?: number;
  }[];
}

export interface PayoffCurvePoint {
  price: number;
  pnl_expiry: number;
  pnl_today: number;
}

export interface StrategyAnalysisResult {
  symbol: string;
  spot: number;
  max_profit_inr: number | null;
  max_loss_inr: number | null;
  is_unlimited_profit: boolean;
  is_unlimited_loss: boolean;
  risk_reward: string;
  breakevens: number[];
  pop_pct: number;
  net_credit_debit_inr: number;
  is_credit: boolean;
  margin_required_inr: number;
  net_greeks: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
  };
  payoff_curve: PayoffCurvePoint[];
}
