"""
Tests — AI Portfolio Orchestrator
===================================
Verifies the core engines (Healer, Causality, Risk-Parity, and 
the full PortfolioManager).
"""

import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, "E:/Trading Platform")

from core.orchestrator.engines.causality_engine import CausalityEngine
from core.orchestrator.engines.risk_parity import RiskParityEngine
from core.orchestrator.engines.healer_engine import HealerEngine, Position
from core.orchestrator.portfolio_manager import PortfolioManager
from core.orchestrator.engines.sentiment_engine import SentimentScore


# ---------------------------------------------------------------------------
# 1. Causality Engine
# ---------------------------------------------------------------------------

class TestCausalityEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CausalityEngine()

    def test_crude_oil_spike(self):
        macro = {"crude_oil_change_pct": 0.05}  # 5% spike
        insights = self.engine.run_causality_check(macro)
        self.assertTrue(any("ASIANPAINT" in i for i in insights))
        self.assertTrue(any("Bearish" in i for i in insights))

    def test_usd_inr_weakness(self):
        macro = {"usd_inr_change_pct": 0.03}  # INR weakened by 3%
        insights = self.engine.run_causality_check(macro)
        self.assertTrue(any("TCS.NS" in i for i in insights))
        self.assertTrue(any("Benefit" in i or "benefiting" in i.lower() or "direct benefit" in i.lower() for i in insights))

    def test_no_macro_triggers(self):
        macro = {"crude_oil_change_pct": 0.01, "usd_inr_change_pct": 0.01}
        insights = self.engine.run_causality_check(macro)
        self.assertEqual(len(insights), 0)


# ---------------------------------------------------------------------------
# 2. Risk-Parity Engine
# ---------------------------------------------------------------------------

class TestRiskParityEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RiskParityEngine()

    def test_panic_vix(self):
        alloc = self.engine.compute_optimal_allocation(30.0)
        self.assertEqual(alloc.equity_pct, 0.30)
        self.assertEqual(alloc.debt_pct, 0.40)
        self.assertEqual(alloc.gold_pct, 0.30)

    def test_complacency_vix(self):
        alloc = self.engine.compute_optimal_allocation(10.0)
        self.assertGreaterEqual(alloc.equity_pct, 0.80)


# ---------------------------------------------------------------------------
# 3. Healer Engine
# ---------------------------------------------------------------------------

class TestHealerEngine(unittest.TestCase):
    def setUp(self):
        # Panic at -15% PnL and <= -0.3 sentiment
        self.engine = HealerEngine(panic_threshold=-0.15, sentiment_threshold=-0.3)

    def test_identifies_and_rotates_weak_link(self):
        damaged_pos = Position(
            ticker="BAD.NS", entry_price=100.0, current_price=80.0,  # -20% PnL
            sentiment_score=-0.5, momentum_score=0.1
        )
        healthy_pos = Position(
            ticker="OKAY.NS", entry_price=100.0, current_price=105.0,
            sentiment_score=0.2, momentum_score=0.4
        )
        
        candidates = [
            Position("STAR.NS", 100, 100, 0.8, 0.9),  # High momentum candidate
            Position("MEH.NS", 100, 100, 0.6, 0.5)
        ]

        actions = self.engine.evaluate_portfolio([damaged_pos, healthy_pos], candidates)
        
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].ticker_to_sell, "BAD.NS")
        self.assertEqual(actions[0].ticker_to_buy, "STAR.NS")
        self.assertIn("Tax-Loss", actions[0].reasoning)

    def test_sells_to_cash_if_no_candidates(self):
        damaged_pos = Position(
            ticker="BAD.NS", entry_price=100.0, current_price=80.0,
            sentiment_score=-0.5, momentum_score=0.1
        )
        actions = self.engine.evaluate_portfolio([damaged_pos], candidates=[])
        self.assertEqual(actions[0].ticker_to_buy, "CASH")


# ---------------------------------------------------------------------------
# 4. Orchestrator Integration (Mocks external calls)
# ---------------------------------------------------------------------------

class TestPortfolioManager(unittest.IsolatedAsyncioTestCase):
    
    @patch('core.orchestrator.portfolio_manager.YFinanceAdapter', autospec=True)
    @patch('core.orchestrator.portfolio_manager.SentimentEngine', autospec=True)
    async def test_orchestration_cycle(self, mock_sentiment_class, mock_yf_class):
        # Setup mocks
        mock_yf_instance = mock_yf_class.return_value
        mock_yf_instance.fetch_macro_snapshot = AsyncMock(return_value={
            "india_vix_close": 26.0,  # Should trigger panic parity
            "crude_oil_change_pct": 0.05
        })

        mock_sentiment_instance = mock_sentiment_class.return_value
        mock_sentiment_instance.analyze_headlines = AsyncMock(
            return_value=SentimentScore("TCS.NS", 0.5, "Bullish", "Good earnings")
        )

        manager = PortfolioManager()
        
        # Override the injected mocks
        manager.yfinance = mock_yf_instance
        manager.sentiment = mock_sentiment_instance

        positions = [
            Position("TCS.NS", 100.0, 105.0, 0.0, 0.5)
        ]
        headlines = {"TCS.NS": ["TCS posts record Q3 profits"]}

        report = await manager.run_orchestration_cycle(positions, [], headlines)

        # Asserts
        self.assertIn("global_macros", report)
        self.assertIn("causality_insights", report)
        
        # VIX was 26.0, should be "Panic" zone (30% equity)
        alloc = report["recommended_allocation"]
        self.assertEqual(alloc["equity"], 0.30)
        self.assertIn("panic", alloc["reason"].lower())

        # Sentiment should have updated
        self.assertIn("TCS.NS", report["sentiment_updates"])
        self.assertEqual(report["sentiment_updates"]["TCS.NS"]["score"], 0.5)

        # Causality should note crude spike
        self.assertTrue(any("Crude" in c for c in report["causality_insights"]))


if __name__ == "__main__":
    unittest.main()
