import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Callable, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Candle:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 100000.0


@dataclass
class Trade:
    entry_date: str
    entry_price: float
    exit_date: Optional[str]
    exit_price: Optional[float]
    side: str  # "LONG" | "SHORT"
    quantity: int
    pnl_inr: float = 0.0
    pnl_pct: float = 0.0
    holding_days: int = 0
    exit_reason: str = ""  # "SIGNAL" | "STOP_LOSS" | "TARGET" | "EOD" | "SEBI_LOCK"


@dataclass
class BacktestResult:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl_inr: float
    max_drawdown_pct: float
    max_drawdown_inr: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    profit_factor: float
    avg_win_inr: float
    avg_loss_inr: float
    max_consecutive_losses: int
    total_brokerage_inr: float
    total_stt_inr: float
    net_pnl_after_costs_inr: float
    annualized_return_pct: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["trades"] = [asdict(t) for t in self.trades]
        return d


class NSEBacktestEngine:
    """
    Institutional Backtesting Engine for Indian Equities and F&O.
    Features:
    - Zero look-ahead bias (strict point-in-time sequential processing).
    - Authentic Indian Statutory Costs: Brokerage, STT, Exchange Turnover Charges,
      SEBI Turnover Charges, Stamp Duty, and 18% GST.
    - SEBI PTRC margin utilization limits and freeze quantity simulation.
    """

    def __init__(self, initial_capital_inr: float = 1_000_000.0, brokerage_per_trade_inr: float = 20.0):
        self.initial_capital = initial_capital_inr
        self.brokerage_flat = brokerage_per_trade_inr
        self.risk_free_rate = 0.0675  # 6.75% 10-Year Indian Government Bond Benchmark

    def calculate_indian_costs(self, trade_val: float, is_sell: bool) -> Dict[str, float]:
        """Calculates exact statutory fee breakdown under Indian tax code."""
        brokerage = min(self.brokerage_flat, trade_val * 0.0003)
        stt = trade_val * 0.00025 if is_sell else 0.0  # STT primarily charged on sell side in derivatives/intraday
        exchange_charges = trade_val * 0.0000325       # NSE cash/derivative turnover fee
        sebi_charges = trade_val * 0.0000010           # ₹10 per crore SEBI turnover fee
        stamp_duty = trade_val * 0.00003 if not is_sell else 0.0  # State stamp duty on buy side
        gst = (brokerage + exchange_charges + sebi_charges) * 0.18  # 18% GST

        total_friction = brokerage + stt + exchange_charges + sebi_charges + stamp_duty + gst
        return {
            "brokerage": brokerage,
            "stt": stt,
            "exchange_charges": exchange_charges,
            "sebi_charges": sebi_charges,
            "stamp_duty": stamp_duty,
            "gst": gst,
            "total_friction": total_friction,
        }

    def run(self, candles: List[Candle], strategy_fn: Callable[[List[Candle]], Dict[str, Any]]) -> BacktestResult:
        """
        Executes point-in-time sequential backtest across the provided candle history.
        """
        if not candles:
            return BacktestResult(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
                total_pnl_inr=0.0, max_drawdown_pct=0.0, max_drawdown_inr=0.0,
                sharpe_ratio=0.0, sortino_ratio=0.0, calmar_ratio=0.0, profit_factor=0.0,
                avg_win_inr=0.0, avg_loss_inr=0.0, max_consecutive_losses=0,
                total_brokerage_inr=0.0, total_stt_inr=0.0, net_pnl_after_costs_inr=0.0,
                annualized_return_pct=0.0,
            )

        capital = self.initial_capital
        equity_curve = [capital]
        trades: List[Trade] = []
        open_trade: Optional[Trade] = None

        total_brokerage = 0.0
        total_stt = 0.0

        for i in range(15, len(candles)):
            # Strictly provide historical slice up to current bar to eliminate look-ahead bias
            historical_slice = candles[: i + 1]
            current_bar = candles[i]

            # Manage existing open position
            if open_trade is not None:
                open_trade.holding_days += 1

                # Check Stop Loss & Target triggers within the bar
                hit_stop = False
                hit_target = False

                if open_trade.side == "LONG":
                    hit_stop = current_bar.low <= open_trade.entry_price * 0.985
                    hit_target = current_bar.high >= open_trade.entry_price * 1.030
                else:
                    hit_stop = current_bar.high >= open_trade.entry_price * 1.015
                    hit_target = current_bar.low <= open_trade.entry_price * 0.970

                should_close = hit_stop or hit_target or open_trade.holding_days >= 5
                if should_close:
                    exit_price = (
                        (open_trade.entry_price * 0.985 if open_trade.side == "LONG" else open_trade.entry_price * 1.015)
                        if hit_stop
                        else (
                            (open_trade.entry_price * 1.030 if open_trade.side == "LONG" else open_trade.entry_price * 0.970)
                            if hit_target
                            else current_bar.close
                        )
                    )
                    reason = "STOP_LOSS" if hit_stop else ("TARGET" if hit_target else "TIME_EXPIRY")

                    trade_val = exit_price * open_trade.quantity
                    costs = self.calculate_indian_costs(trade_val, is_sell=(open_trade.side == "LONG"))
                    total_brokerage += costs["brokerage"]
                    total_stt += costs["stt"]

                    if open_trade.side == "LONG":
                        gross_pnl = (exit_price - open_trade.entry_price) * open_trade.quantity
                    else:
                        gross_pnl = (open_trade.entry_price - exit_price) * open_trade.quantity

                    net_pnl = gross_pnl - costs["total_friction"]
                    open_trade.exit_date = current_bar.date
                    open_trade.exit_price = round(exit_price, 2)
                    open_trade.pnl_inr = round(net_pnl, 2)
                    open_trade.pnl_pct = round((gross_pnl / (open_trade.entry_price * open_trade.quantity)) * 100, 2)
                    open_trade.exit_reason = reason

                    capital += net_pnl
                    trades.append(open_trade)
                    open_trade = None

            # Evaluate strategy on closed bars
            if open_trade is None:
                signal = strategy_fn(historical_slice)
                action = signal.get("action", "HOLD")
                quantity = int(signal.get("quantity", 50))  # Standard 1 Nifty lot

                # BankNifty freeze quantity check
                if "BANKNIFTY" in str(signal.get("ticker", "")) and quantity > 900:
                    quantity = 900

                # Margin check (SEBI 85% rule)
                required_margin = current_bar.close * quantity * 0.15  # Derivative margin proxy
                if action in ["BUY", "SELL"] and (required_margin / max(1.0, capital)) <= 0.85:
                    entry_costs = self.calculate_indian_costs(current_bar.close * quantity, is_sell=(action == "SELL"))
                    total_brokerage += entry_costs["brokerage"]
                    total_stt += entry_costs["stt"]
                    capital -= entry_costs["total_friction"]

                    open_trade = Trade(
                        entry_date=current_bar.date,
                        entry_price=current_bar.close,
                        exit_date=None,
                        exit_price=None,
                        side="LONG" if action == "BUY" else "SHORT",
                        quantity=quantity,
                    )

            equity_curve.append(round(capital, 2))

        # Close out any remaining position at end of data
        if open_trade is not None:
            last_bar = candles[-1]
            trade_val = last_bar.close * open_trade.quantity
            costs = self.calculate_indian_costs(trade_val, is_sell=(open_trade.side == "LONG"))
            gross_pnl = (last_bar.close - open_trade.entry_price) * open_trade.quantity if open_trade.side == "LONG" else (open_trade.entry_price - last_bar.close) * open_trade.quantity
            open_trade.exit_date = last_bar.date
            open_trade.exit_price = last_bar.close
            open_trade.pnl_inr = round(gross_pnl - costs["total_friction"], 2)
            open_trade.pnl_pct = round((gross_pnl / (open_trade.entry_price * open_trade.quantity)) * 100, 2)
            open_trade.exit_reason = "EOD_FORCE_CLOSE"
            capital += open_trade.pnl_inr
            trades.append(open_trade)

        # Performance analytics computation
        winning = [t for t in trades if t.pnl_inr > 0]
        losing = [t for t in trades if t.pnl_inr <= 0]
        win_rate = round(len(winning) / max(1, len(trades)) * 100, 1)

        total_pnl = capital - self.initial_capital
        eq_arr = np.array(equity_curve)
        peak = np.maximum.accumulate(eq_arr)
        drawdown_arr = (peak - eq_arr)
        max_dd_inr = float(np.max(drawdown_arr)) if len(drawdown_arr) > 0 else 0.0
        max_dd_pct = float(np.max(drawdown_arr / np.maximum(1.0, peak)) * 100.0) if len(drawdown_arr) > 0 else 0.0

        # Daily returns for Sharpe / Sortino
        if len(equity_curve) >= 2:
            daily_returns = np.diff(eq_arr) / eq_arr[:-1]
            ann_factor = np.sqrt(252.0)
            excess_daily = daily_returns - (self.risk_free_rate / 252.0)
            std_daily = np.std(daily_returns)
            sharpe = float(np.mean(excess_daily) / std_daily * ann_factor) if std_daily > 1e-6 else 0.0

            downside = daily_returns[daily_returns < 0]
            downside_std = np.std(downside) if len(downside) > 0 else 1e-4
            sortino = float(np.mean(excess_daily) / downside_std * ann_factor) if downside_std > 1e-6 else 0.0

            duration_years = max(0.1, len(candles) / 252.0)
            ann_ret = float(((capital / self.initial_capital) ** (1.0 / duration_years) - 1.0) * 100.0)
            calmar = float(ann_ret / max(0.1, max_dd_pct))
        else:
            sharpe, sortino, calmar, ann_ret = 0.0, 0.0, 0.0, 0.0

        gross_wins = sum(t.pnl_inr for t in winning)
        gross_losses = abs(sum(t.pnl_inr for t in losing))
        profit_factor = round(gross_wins / max(1.0, gross_losses), 2)

        # Max consecutive losses
        consec_losses = 0
        max_consec = 0
        for t in trades:
            if t.pnl_inr <= 0:
                consec_losses += 1
                max_consec = max(max_consec, consec_losses)
            else:
                consec_losses = 0

        return BacktestResult(
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=win_rate,
            total_pnl_inr=round(total_pnl, 2),
            max_drawdown_pct=round(max_dd_pct, 2),
            max_drawdown_inr=round(max_dd_inr, 2),
            sharpe_ratio=round(sharpe, 2),
            sortino_ratio=round(sortino, 2),
            calmar_ratio=round(calmar, 2),
            profit_factor=profit_factor,
            avg_win_inr=round(float(np.mean([t.pnl_inr for t in winning])) if winning else 0.0, 2),
            avg_loss_inr=round(float(np.mean([t.pnl_inr for t in losing])) if losing else 0.0, 2),
            max_consecutive_losses=max_consec,
            total_brokerage_inr=round(total_brokerage, 2),
            total_stt_inr=round(total_stt, 2),
            net_pnl_after_costs_inr=round(total_pnl, 2),
            annualized_return_pct=round(ann_ret, 2),
            trades=trades,
            equity_curve=equity_curve,
        )
