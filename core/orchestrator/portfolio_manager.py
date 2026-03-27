"""
Portfolio Manager (AI Orchestration Core)
==========================================
The central brain that coordinates the Sentiment, Causality, RL, Risk Parity, 
and Healer engines to build a comprehensive view of the market and issue 
portfolio-level rotation/rebalancing commands.
"""

import logging
from typing import Dict, Any, List

from data.adapters.yfinance_adapter import YFinanceAdapter
from core.orchestrator.engines.sentiment_engine import SentimentEngine, SentimentScore
from core.orchestrator.engines.causality_engine import CausalityEngine
from core.orchestrator.engines.risk_parity import RiskParityEngine
from core.orchestrator.engines.healer_engine import HealerEngine, Position
from core.orchestrator.engines.rl_manager import RLManager

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Autonomous AI Portfolio Orchestrator.
    Max Profit, Min Loss, Automated Recovery.
    """

    def __init__(self):
        # 1. Initialize Adapters
        self.yfinance = YFinanceAdapter()

        # 2. Initialize the 5 AI Engines
        self.sentiment = SentimentEngine()
        self.causality = CausalityEngine()
        self.risk_parity = RiskParityEngine()
        self.healer = HealerEngine()
        self.rl_manager = RLManager(atr_multiplier=2.0)

        logger.info("⚡ PortfolioManager Orchestrator Base Online.")

    async def run_orchestration_cycle(self, positions: List[Position], candidates: List[Position], headlines: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Executes a full top-down macro-to-micro orchestration cycle.
        Called e.g., daily at open/close or intraday on massive volatility spikes.
        """
        logger.info("Starting Orchestration Cycle…")
        report = {}

        # ------------------------------------------------------------------
        # STEP 1: Global Macro & Causality
        # ------------------------------------------------------------------
        macros = await self.yfinance.fetch_macro_snapshot()
        report["global_macros"] = macros
        
        causal_insights = self.causality.run_causality_check(macros)
        report["causality_insights"] = causal_insights

        # ------------------------------------------------------------------
        # STEP 2: Risk-Parity Allocation
        # ------------------------------------------------------------------
        current_vix = macros.get("india_vix_close", 15.0)  # Default to normal 15 if API fails
        allocation = self.risk_parity.compute_optimal_allocation(current_vix)
        report["recommended_allocation"] = {
            "equity": allocation.equity_pct,
            "debt": allocation.debt_pct,
            "gold": allocation.gold_pct,
            "reason": allocation.reason
        }

        # ------------------------------------------------------------------
        # STEP 3: News / FinBERT Sentiment Update
        # ------------------------------------------------------------------
        sentiment_updates = {}
        for pos in positions:
            if headlines.get(pos.ticker):
                score_obj = await self.sentiment.analyze_headlines(pos.ticker, headlines[pos.ticker])
                pos.sentiment_score = score_obj.score  # Update the live position object
                sentiment_updates[pos.ticker] = {"score": score_obj.score, "label": score_obj.label}
        
        report["sentiment_updates"] = sentiment_updates

        # ------------------------------------------------------------------
        # STEP 4: Portfolio Healing (Tax-Loss Rotation)
        # ------------------------------------------------------------------
        # Healer scans the dynamically updated Sentiment scores
        recovery_actions = self.healer.evaluate_portfolio(positions, candidates)
        report["healer_rotations"] = [{"sell": a.ticker_to_sell, "buy": a.ticker_to_buy, "reason": a.reasoning} for a in recovery_actions]

        # ------------------------------------------------------------------
        # STEP 5: PPO / RL Sizing Prediction (Stub)
        # ------------------------------------------------------------------
        state = {"vix": current_vix, "positions_count": len(positions)}
        rl_action = self.rl_manager.predict_action(state)
        report["rl_manager_stance"] = rl_action

        # Complete
        logger.info("🟢 Orchestration Cycle Complete.")
        return report
