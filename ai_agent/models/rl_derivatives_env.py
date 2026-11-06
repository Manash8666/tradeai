"""
Indian Derivatives Reinforcement Learning Environment (FinRL-Meta Architecture).
Proprietary Farama Gymnasium / OpenAI Gym compliant F&O environment calibrated
for Indian Equity & Index Derivatives (NSE NIFTY50 & BANKNIFTY).

Observation Space:
- Spot, ATM IV, Volatility Skew, PCR OI, Net Delta, Gamma, Theta, Vega, 5m Returns, Volume Delta, Margin Usage %.

Action Space:
- Discrete actions covering 8 institutional derivative allocations:
  0: HOLD / FLAT
  1: BUY_ATM_CALL
  2: BUY_ATM_PUT
  3: BULL_CALL_SPREAD
  4: BEAR_PUT_SPREAD
  5: SHORT_STRADDLE
  6: IRON_CONDOR
  7: SQUARE_OFF_ALL

Reward:
- Differential Sharpe Ratio penalizing transaction costs (STT 0.1%, Brokerage ₹20, GST 18%, Turnover Fees)
  and maximum drawdown variance.
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional, List


class IndianDerivativesEnv:
    """
    High-throughput Reinforcement Learning environment for Indian F&O trading.
    Implements standard step(), reset(), and state extraction compatible with Stable-Baselines3,
    RLlib, and FinRL algorithms.
    """

    def __init__(
        self,
        symbol: str = "NIFTY",
        initial_capital_inr: float = 10_000_000.0,  # ₹1 Crore Institutional Pool
        lot_size: int = 50,
        max_steps: int = 375,  # 375 1-minute steps per Indian trading day (09:15 to 15:30)
    ):
        self.symbol = symbol
        self.initial_capital_inr = initial_capital_inr
        self.lot_size = lot_size
        self.max_steps = max_steps

        # State dimensions: 11 normalized financial features
        self.observation_space_shape = (11,)
        # 8 discrete strategy actions
        self.action_space_n = 8

        # Execution Fee Constants (SEBI / Indian Exchange Mandates)
        self.brokerage_per_order_inr = 20.0
        self.stt_rate = 0.001  # 0.1% STT on option sell side
        self.turnover_fee_rate = 0.000035  # NSE exchange turnover fee
        self.gst_rate = 0.18  # 18% GST on brokerage + turnover fees

        self.reset()

    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Resets the environment for a new trading episode."""
        if seed is not None:
            np.random.seed(seed)

        self.step_idx = 0
        self.current_capital_inr = self.initial_capital_inr
        self.portfolio_pnl_inr = 0.0
        self.peak_capital_inr = self.initial_capital_inr
        self.positions: List[Dict[str, Any]] = []

        # Market state simulation initialized at benchmark prices
        self.spot = 23806.95 if self.symbol == "NIFTY" else 51240.20
        self.iv = 0.1581  # 15.81% VIX
        self.pcr = 1.05
        self.skew = 0.012

        self.returns_history: List[float] = []

        obs = self._get_observation()
        info = {
            "step": self.step_idx,
            "capital_inr": self.current_capital_inr,
            "symbol": self.symbol,
            "status": "INITIALIZED",
        }
        return obs, info

    def _get_observation(self) -> np.ndarray:
        """Returns the normalized 11-dimensional observation vector."""
        # 1. Spot change normalized to 20,000 baseline
        norm_spot = (self.spot - 20000.0) / 5000.0
        # 2. IV normalized around 15%
        norm_iv = (self.iv - 0.15) / 0.10
        # 3. Volatility Skew
        norm_skew = self.skew * 50.0
        # 4. PCR OI (Put-Call Ratio) around 1.0
        norm_pcr = self.pcr - 1.0
        # 5-8. Net Portfolio Greeks
        net_delta = sum(p.get("delta", 0.0) for p in self.positions)
        net_gamma = sum(p.get("gamma", 0.0) for p in self.positions)
        net_theta = sum(p.get("theta", 0.0) for p in self.positions) / 1000.0
        net_vega = sum(p.get("vega", 0.0) for p in self.positions) / 1000.0
        # 9. Recent 5-step return
        ret_5 = sum(self.returns_history[-5:]) if len(self.returns_history) >= 5 else 0.0
        # 10. Volume Delta proxy
        vol_delta = np.sin(self.step_idx / 10.0) * 0.5
        # 11. Margin Utilization % (0.0 to 1.0)
        margin_used = sum(p.get("margin_inr", 0.0) for p in self.positions)
        norm_margin = min(1.0, margin_used / max(1.0, self.current_capital_inr))

        obs = np.array(
            [
                norm_spot,
                norm_iv,
                norm_skew,
                norm_pcr,
                net_delta,
                net_gamma,
                net_theta,
                net_vega,
                ret_5,
                vol_delta,
                norm_margin,
            ],
            dtype=np.float32,
        )
        return obs

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Executes one environment step.
        action: integer from 0 to 7
        Returns: observation, reward, terminated, truncated, info
        """
        self.step_idx += 1

        # Simulate market price evolution (geometric Brownian motion with jump noise)
        drift = 0.0001
        vol = self.iv / np.sqrt(252 * 375)
        shock = np.random.normal(drift, vol)
        price_change = self.spot * shock
        self.spot += price_change

        # Update IV and PCR stochastic dynamics
        self.iv = max(0.08, min(0.40, self.iv + np.random.normal(0, 0.001)))
        self.pcr = max(0.5, min(1.8, self.pcr + np.random.normal(0, 0.01)))

        # Process Action and Calculate Transaction Costs
        tx_cost_inr = 0.0
        action_name = "HOLD"

        if action == 1:  # BUY_ATM_CALL
            action_name = "BUY_ATM_CALL"
            premium = self.spot * 0.012
            cost = premium * self.lot_size
            tx_cost_inr = self.brokerage_per_order_inr + (cost * self.turnover_fee_rate * (1 + self.gst_rate))
            self.positions.append({
                "type": "CALL",
                "entry_spot": self.spot,
                "premium": premium,
                "qty": self.lot_size,
                "delta": 0.50,
                "margin_inr": cost,
            })
        elif action == 2:  # BUY_ATM_PUT
            action_name = "BUY_ATM_PUT"
            premium = self.spot * 0.012
            cost = premium * self.lot_size
            tx_cost_inr = self.brokerage_per_order_inr + (cost * self.turnover_fee_rate * (1 + self.gst_rate))
            self.positions.append({
                "type": "PUT",
                "entry_spot": self.spot,
                "premium": premium,
                "qty": self.lot_size,
                "delta": -0.50,
                "margin_inr": cost,
            })
        elif action == 3:  # BULL_CALL_SPREAD
            action_name = "BULL_CALL_SPREAD"
            net_debit = self.spot * 0.005 * self.lot_size
            tx_cost_inr = (self.brokerage_per_order_inr * 2) + (net_debit * self.turnover_fee_rate * 1.18)
            self.positions.append({
                "type": "SPREAD",
                "entry_spot": self.spot,
                "net_debit": net_debit,
                "qty": self.lot_size,
                "delta": 0.22,
                "margin_inr": net_debit * 1.5,
            })
        elif action == 4:  # BEAR_PUT_SPREAD
            action_name = "BEAR_PUT_SPREAD"
            net_debit = self.spot * 0.005 * self.lot_size
            tx_cost_inr = (self.brokerage_per_order_inr * 2) + (net_debit * self.turnover_fee_rate * 1.18)
            self.positions.append({
                "type": "SPREAD",
                "entry_spot": self.spot,
                "net_debit": net_debit,
                "qty": self.lot_size,
                "delta": -0.22,
                "margin_inr": net_debit * 1.5,
            })
        elif action == 5:  # SHORT_STRADDLE
            action_name = "SHORT_STRADDLE"
            credit = self.spot * 0.024 * self.lot_size
            margin = self.spot * self.lot_size * 0.12  # 12% SPAN
            tx_cost_inr = (self.brokerage_per_order_inr * 2) + (credit * self.stt_rate)
            self.positions.append({
                "type": "STRADDLE",
                "entry_spot": self.spot,
                "credit": credit,
                "qty": self.lot_size,
                "delta": 0.0,
                "margin_inr": margin,
            })
        elif action == 6:  # IRON_CONDOR
            action_name = "IRON_CONDOR"
            credit = self.spot * 0.008 * self.lot_size
            margin = self.spot * self.lot_size * 0.04  # Defined risk SPAN relief
            tx_cost_inr = (self.brokerage_per_order_inr * 4) + (credit * self.stt_rate)
            self.positions.append({
                "type": "IRON_CONDOR",
                "entry_spot": self.spot,
                "credit": credit,
                "qty": self.lot_size,
                "delta": 0.0,
                "margin_inr": margin,
            })
        elif action == 7:  # SQUARE_OFF_ALL
            action_name = "SQUARE_OFF_ALL"
            if self.positions:
                tx_cost_inr = self.brokerage_per_order_inr * len(self.positions)
                self.positions.clear()

        # Update step PnL from open positions
        step_pnl = 0.0
        for p in self.positions:
            if p["type"] == "CALL":
                step_pnl += (price_change) * (p["qty"])
            elif p["type"] == "PUT":
                step_pnl -= (price_change) * (p["qty"])
            elif p["type"] == "SPREAD":
                step_pnl += (price_change * 0.5) * (p["qty"])
            elif p["type"] in ["STRADDLE", "IRON_CONDOR"]:
                # Theta decay gain minus gamma loss on big moves
                theta_gain = 45.0
                gamma_loss = abs(price_change) * 0.8
                step_pnl += (theta_gain - gamma_loss)

        # Net step profit minus transaction costs
        net_step_pnl = step_pnl - tx_cost_inr
        self.portfolio_pnl_inr += net_step_pnl
        self.current_capital_inr += net_step_pnl
        self.peak_capital_inr = max(self.peak_capital_inr, self.current_capital_inr)

        step_return = net_step_pnl / max(1.0, self.initial_capital_inr)
        self.returns_history.append(step_return)

        # Drawdown calculation
        drawdown = (self.peak_capital_inr - self.current_capital_inr) / max(1.0, self.peak_capital_inr)

        # Reward: Differential return penalized by drawdown and transaction friction
        reward = step_return * 100.0 - (drawdown * 2.0) - (tx_cost_inr / 500.0)

        # Termination checks
        terminated = False
        truncated = False

        # Ruin condition or max loss limit (3% stop out)
        if drawdown > 0.03:
            terminated = True
            reward -= 10.0  # Big penalty for hitting max risk limit

        if self.step_idx >= self.max_steps:
            truncated = True

        obs = self._get_observation()
        info = {
            "step": self.step_idx,
            "action": action_name,
            "net_pnl_inr": round(self.portfolio_pnl_inr, 2),
            "capital_inr": round(self.current_capital_inr, 2),
            "drawdown_pct": round(drawdown * 100.0, 2),
            "spot": round(self.spot, 2),
            "active_positions_count": len(self.positions),
        }

        return obs, float(reward), terminated, truncated, info


# Singleton environment instance
indian_fno_env = IndianDerivativesEnv()
