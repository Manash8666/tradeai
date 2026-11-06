"""
Proprietary NSE/BSE Backtesting Engine.
No look-ahead bias. Realistic Indian market simulation including STT, brokerage, and SEBI margin rules.
"""
from .nse_backtest_engine import NSEBacktestEngine, Candle, Trade, BacktestResult
from .robustness_scorer import WalkForwardRobustnessScorer, RobustnessReport

__all__ = [
    "NSEBacktestEngine",
    "Candle",
    "Trade",
    "BacktestResult",
    "WalkForwardRobustnessScorer",
    "RobustnessReport",
]
