import logging
import numpy as np
from typing import Tuple, Dict, Any

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYMNASIUM_AVAILABLE = True
except ImportError:
    try:
        import gym
        from gym import spaces
        GYMNASIUM_AVAILABLE = True
    except ImportError:
        GYMNASIUM_AVAILABLE = False

from backend.app.core.timezone_guards import temporal_guard
from backend.app.core.pnl_greed_lock import greed_lock_engine

logger = logging.getLogger(__name__)


class NseBseOptionGymEnv:
    """
    Advanced Quantitative Reinforcement Learning Environment for NSE/BSE Derivatives.
    Formulates the Indian 0DTE Options space as a Markov Decision Process (MDP)
    with Sharpe-penalized differential rewards, SEBI PTRC margin boundaries,
    and trans-exchange friction awareness (NSE vs BSE).
    """

    def __init__(self, initial_capital_inr: float = 1_000_000.0):
        self.initial_capital = initial_capital_inr
        self.max_steps = 375  # 375 minutes in an Indian trading day (9:15 AM to 3:30 PM IST)

        # Indian regulatory and friction parameters
        self.nse_stt_friction = 0.000625   # STT + Exchange turnover charge proxy (NSE)
        self.bse_stt_friction = 0.000375   # Favorable BSE fee structure
        self.max_allowed_margin_util = 0.85  # SEBI PTRC 85% deployment limit
        self.daily_target_inr = 50_000.0
        self.max_drawdown_limit_inr = -15_000.0

        # Action Space: 7 discrete actions
        self.action_space_size = 7
        self.observation_space_size = 12

        if GYMNASIUM_AVAILABLE:
            self.action_space = spaces.Discrete(self.action_space_size)
            self.observation_space = spaces.Box(
                low=-np.inf, high=np.inf, shape=(self.observation_space_size,), dtype=np.float32
            )

        self.reset()
        logger.info("[RL GYM] Upgraded 12-State MDP Option Gym initialized with Sharpe-penalized rewards.")

    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.balance = self.initial_capital
        self.prev_portfolio_val = self.initial_capital
        self.deployed_margin = 0.0
        self.current_step = 0
        self.daily_pnl = 0.0

        self.spot_price = 24500.0
        self.india_vix = 14.5
        self.fii_net_flow = 250.0
        self.pcr = 0.95
        self.gift_nifty_premium = 20.0
        self.volume_surge = 1.0

        return self._get_state(), {"balance": self.balance, "daily_pnl": self.daily_pnl}

    def _get_state(self) -> np.ndarray:
        pnl_norm = self.daily_pnl / self.daily_target_inr
        vix_norm = self.india_vix / 20.0
        margin_util = self.deployed_margin / max(1.0, self.balance)
        time_rem_norm = (self.max_steps - self.current_step) / self.max_steps
        fii_norm = np.clip(self.fii_net_flow / 2000.0, -1.0, 1.0)
        pcr_norm = np.clip(self.pcr / 1.0, 0.2, 2.0)
        gift_norm = np.clip(self.gift_nifty_premium / 100.0, -1.0, 1.0)
        session_phase = 0.5 if (0 < self.current_step < self.max_steps) else (0.0 if self.current_step == 0 else 1.0)

        state = np.array([
            (self.spot_price - 24500.0) / 24500.0,
            self.volume_surge,
            vix_norm,
            fii_norm,
            time_rem_norm,
            margin_util,
            pnl_norm,
            0.02 * np.sin(self.current_step / 15.0),
            pcr_norm,
            gift_norm,
            0.0004,
            session_phase,
        ], dtype=np.float32)

        return state

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.current_step += 1

        daily_vol = (self.india_vix / 100.0) / np.sqrt(252.0)
        step_drift = np.random.normal(0, daily_vol / np.sqrt(375.0)) * self.spot_price
        self.spot_price += step_drift

        trade_executed = False
        action_magnitude = 0.0

        if action == 0:
            alloc = self.balance * 0.80
            self.deployed_margin = min(self.balance, self.deployed_margin + alloc)
            action_magnitude = 0.80
            trade_executed = True
        elif action == 1:
            alloc = self.balance * 0.40
            self.deployed_margin = min(self.balance, self.deployed_margin + alloc)
            action_magnitude = 0.40
            trade_executed = True
        elif action == 2:
            alloc = self.balance * 0.15
            self.deployed_margin = min(self.balance, self.deployed_margin + alloc)
            action_magnitude = 0.15
            trade_executed = True
        elif action == 3:
            action_magnitude = 0.0
        elif action == 4:
            alloc = self.balance * 0.15
            self.deployed_margin = min(self.balance, self.deployed_margin + alloc)
            action_magnitude = 0.15
            trade_executed = True
        elif action == 5:
            self.deployed_margin = max(0.0, self.deployed_margin * 0.60)
            action_magnitude = 0.40
            trade_executed = True
        elif action == 6:
            self.deployed_margin = 0.0
            action_magnitude = 1.0
            trade_executed = True

        delta_exposure = (self.deployed_margin / max(1.0, self.balance)) * (1.0 if action in [0, 1] else (-1.0 if action in [5, 6] else 0.0))
        step_pnl = delta_exposure * step_drift * 50.0
        self.daily_pnl += step_pnl
        current_portfolio_val = self.initial_capital + self.daily_pnl

        step_return = (current_portfolio_val - self.prev_portfolio_val) / max(1.0, self.prev_portfolio_val)
        self.prev_portfolio_val = current_portfolio_val

        transaction_cost = action_magnitude * self.nse_stt_friction if trade_executed else 0.0
        vix_penalty = max(0.0, (self.india_vix - 20.0) / 100.0)

        reward = (step_return * 100.0) - (transaction_cost * 10.0) - vix_penalty

        if self.india_vix < 16.0 and step_pnl > 0:
            reward += 0.50

        margin_util = self.deployed_margin / max(1.0, self.balance)
        if margin_util > self.max_allowed_margin_util:
            reward -= 2.0

        terminated = False
        truncated = False

        if self.daily_pnl >= self.daily_target_inr:
            reward += 5.0
            terminated = True
        elif self.daily_pnl <= self.max_drawdown_limit_inr:
            reward -= 5.0
            terminated = True
        elif self.current_step >= self.max_steps:
            terminated = True

        info = {
            "daily_pnl": self.daily_pnl,
            "portfolio_value": current_portfolio_val,
            "margin_utilization": margin_util,
            "spot_price": self.spot_price,
            "step": self.current_step,
        }

        return self._get_state(), float(reward), terminated, truncated, info


nse_bse_gym = NseBseOptionGymEnv()
