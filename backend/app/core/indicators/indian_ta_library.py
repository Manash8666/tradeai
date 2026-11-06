import logging
from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SignalResult:
    value: float
    signal: str  # "BUY", "SELL", "NEUTRAL"
    strength: float  # 0.0 to 1.0
    rationale: str = ""


class IndianTALibrary:
    """
    Comprehensive, zero-dependency Technical Analysis Library built with pure NumPy.
    Optimized for high-frequency NSE/BSE derivative calculations, Max Pain estimation,
    and Indian volatility metrics.
    """

    # -------------------------------------------------------------------------
    # Standard Core Indicators
    # -------------------------------------------------------------------------

    @staticmethod
    def sma(data: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average."""
        data = np.asarray(data, dtype=float)
        if len(data) < period:
            return np.full_like(data, np.nan)
        weights = np.ones(period) / period
        return np.convolve(data, weights, mode="same")

    @staticmethod
    def ema(data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average."""
        data = np.asarray(data, dtype=float)
        if len(data) == 0:
            return np.array([])
        alpha = 2.0 / (period + 1.0)
        ema_arr = np.empty_like(data)
        ema_arr[0] = data[0]
        for i in range(1, len(data)):
            ema_arr[i] = alpha * data[i] + (1.0 - alpha) * ema_arr[i - 1]
        return ema_arr

    @staticmethod
    def rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
        """Wilder's Relative Strength Index."""
        closes = np.asarray(closes, dtype=float)
        if len(closes) <= period:
            return np.full_like(closes, 50.0)

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        rsi_arr = np.zeros(len(closes))
        rsi_arr[:period] = 50.0

        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                rsi_arr[i + 1] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi_arr[i + 1] = 100.0 - (100.0 / (1.0 + rs))

        return rsi_arr

    @staticmethod
    def macd(closes: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Moving Average Convergence Divergence."""
        fast_ema = IndianTALibrary.ema(closes, fast)
        slow_ema = IndianTALibrary.ema(closes, slow)
        macd_line = fast_ema - slow_ema
        signal_line = IndianTALibrary.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands."""
        middle = IndianTALibrary.sma(closes, period)
        std = np.zeros_like(closes)
        for i in range(period - 1, len(closes)):
            std[i] = np.std(closes[i - period + 1 : i + 1])
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        return upper, middle, lower

    @staticmethod
    def atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
        """Average True Range."""
        highs = np.asarray(highs, dtype=float)
        lows = np.asarray(lows, dtype=float)
        closes = np.asarray(closes, dtype=float)

        tr = np.zeros(len(closes))
        tr[0] = highs[0] - lows[0]
        for i in range(1, len(closes)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i - 1])
            lc = abs(lows[i] - closes[i - 1])
            tr[i] = max(hl, hc, lc)

        return IndianTALibrary.ema(tr, period)

    @staticmethod
    def stochastic(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, k_period: int = 14, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Stochastic Oscillator (%K and %D)."""
        k = np.zeros(len(closes))
        for i in range(k_period - 1, len(closes)):
            low_k = np.min(lows[i - k_period + 1 : i + 1])
            high_k = np.max(highs[i - k_period + 1 : i + 1])
            span = max(1e-5, high_k - low_k)
            k[i] = ((closes[i] - low_k) / span) * 100.0
        d = IndianTALibrary.sma(k, d_period)
        return k, d

    @staticmethod
    def vwap(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Volume Weighted Average Price."""
        typical = (highs + lows + closes) / 3.0
        cum_vp = np.cumsum(typical * volumes)
        cum_vol = np.cumsum(volumes)
        return np.where(cum_vol > 0, cum_vp / cum_vol, typical)

    @staticmethod
    def obv(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """On-Balance Volume."""
        obv_arr = np.zeros(len(closes))
        obv_arr[0] = volumes[0]
        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                obv_arr[i] = obv_arr[i - 1] + volumes[i]
            elif closes[i] < closes[i - 1]:
                obv_arr[i] = obv_arr[i - 1] - volumes[i]
            else:
                obv_arr[i] = obv_arr[i - 1]
        return obv_arr

    @staticmethod
    def adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Average Directional Index (ADX, +DI, -DI)."""
        tr = IndianTALibrary.atr(highs, lows, closes, period)
        plus_dm = np.zeros(len(closes))
        minus_dm = np.zeros(len(closes))

        for i in range(1, len(closes)):
            up_move = highs[i] - highs[i - 1]
            down_move = lows[i - 1] - lows[i]
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move

        smoothed_plus = IndianTALibrary.ema(plus_dm, period)
        smoothed_minus = IndianTALibrary.ema(minus_dm, period)

        plus_di = 100.0 * np.where(tr > 0, smoothed_plus / tr, 0.0)
        minus_di = 100.0 * np.where(tr > 0, smoothed_minus / tr, 0.0)

        di_sum = plus_di + minus_di
        dx = 100.0 * np.where(di_sum > 0, np.abs(plus_di - minus_di) / di_sum, 0.0)
        adx_val = IndianTALibrary.ema(dx, period)

        return adx_val, plus_di, minus_di

    @staticmethod
    def supertrend(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 7, multiplier: float = 3.0) -> Tuple[np.ndarray, np.ndarray]:
        """SuperTrend Indicator."""
        atr_val = IndianTALibrary.atr(highs, lows, closes, period)
        hl2 = (highs + lows) / 2.0
        upper_band = hl2 + multiplier * atr_val
        lower_band = hl2 - multiplier * atr_val

        supertrend_arr = np.zeros(len(closes))
        direction_arr = np.ones(len(closes))  # 1 = Bullish, -1 = Bearish

        for i in range(1, len(closes)):
            if closes[i] > upper_band[i - 1]:
                direction_arr[i] = 1
            elif closes[i] < lower_band[i - 1]:
                direction_arr[i] = -1
            else:
                direction_arr[i] = direction_arr[i - 1]

            supertrend_arr[i] = lower_band[i] if direction_arr[i] == 1 else upper_band[i]

        return supertrend_arr, direction_arr

    @staticmethod
    def cci(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 20) -> np.ndarray:
        """Commodity Channel Index."""
        tp = (highs + lows + closes) / 3.0
        sma_tp = IndianTALibrary.sma(tp, period)
        mean_dev = np.zeros_like(tp)
        for i in range(period - 1, len(tp)):
            mean_dev[i] = np.mean(np.abs(tp[i - period + 1 : i + 1] - sma_tp[i]))
        return np.where(mean_dev > 0, (tp - sma_tp) / (0.015 * mean_dev), 0.0)

    @staticmethod
    def williams_r(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
        """Williams %R."""
        wr = np.zeros(len(closes))
        for i in range(period - 1, len(closes)):
            hh = np.max(highs[i - period + 1 : i + 1])
            ll = np.min(lows[i - period + 1 : i + 1])
            span = max(1e-5, hh - ll)
            wr[i] = ((hh - closes[i]) / span) * -100.0
        return wr

    # -------------------------------------------------------------------------
    # NSE / BSE Specific Proprietary Indicators
    # -------------------------------------------------------------------------

    @staticmethod
    def india_vix_regime(india_vix: float) -> SignalResult:
        """Maps India VIX to structured institutional action signals."""
        if india_vix < 13.0:
            return SignalResult(india_vix, "BUY", 0.85, "Ultra-low volatility regime. Options premiums low; momentum breakout favored.")
        elif 13.0 <= india_vix < 18.0:
            return SignalResult(india_vix, "BUY", 0.60, "Normal market vol. Standard trend-following strategies optimal.")
        elif 18.0 <= india_vix < 22.0:
            return SignalResult(india_vix, "NEUTRAL", 0.40, "Elevated volatility. Tighten position sizing; delta-neutral preferred.")
        elif 22.0 <= india_vix < 28.0:
            return SignalResult(india_vix, "SELL", 0.70, "High volatility alert. Defensive puts or tactical cash position mandatory.")
        else:
            return SignalResult(india_vix, "SELL", 0.95, "Extreme volatility crisis (VIX >= 28). Immediate capital preservation halt.")

    @staticmethod
    def option_pain_level(strike_prices: np.ndarray, open_interest_calls: np.ndarray, open_interest_puts: np.ndarray) -> float:
        """Calculates Max Pain strike where option writers have minimal cumulative loss."""
        strikes = np.asarray(strike_prices, dtype=float)
        calls = np.asarray(open_interest_calls, dtype=float)
        puts = np.asarray(open_interest_puts, dtype=float)

        min_loss = float("inf")
        max_pain_strike = strikes[len(strikes) // 2] if len(strikes) > 0 else 0.0

        for strike in strikes:
            call_loss = np.sum(np.maximum(0.0, strike - strikes) * calls)
            put_loss = np.sum(np.maximum(0.0, strikes - strike) * puts)
            total_loss = call_loss + put_loss
            if total_loss < min_loss:
                min_loss = total_loss
                max_pain_strike = strike

        return float(max_pain_strike)

    @staticmethod
    def gift_nifty_gap_signal(gift_nifty_price: float, prev_nse_close: float) -> SignalResult:
        """Analyzes pre-open Asian synthetic arbitrage gap."""
        gap_pct = (gift_nifty_price - prev_nse_close) / max(1.0, prev_nse_close)
        gap_pts = gift_nifty_price - prev_nse_close

        if gap_pct >= 0.007:
            return SignalResult(gap_pts, "BUY", 0.80, f"Strong gap-up indicated (+{gap_pts:.1f} pts, +{gap_pct*100:.2f}%). Watch pre-open auction.")
        elif gap_pct <= -0.007:
            return SignalResult(gap_pts, "SELL", 0.80, f"Severe gap-down indicated ({gap_pts:.1f} pts, {gap_pct*100:.2f}%). High open risk.")
        else:
            return SignalResult(gap_pts, "NEUTRAL", 0.30, f"Flat/moderate opening expected ({gap_pts:+.1f} pts).")

    @staticmethod
    def fii_pcr_signal(pcr: float) -> SignalResult:
        """Evaluates Indian market Put-Call Ratio dynamics."""
        if pcr < 0.70:
            return SignalResult(pcr, "SELL", 0.75, "PCR severely overbought (<0.70). High probability of institutional profit taking.")
        elif pcr > 1.35:
            return SignalResult(pcr, "BUY", 0.75, "PCR deeply oversold (>1.35). High probability of short-covering rally.")
        else:
            return SignalResult(pcr, "NEUTRAL", 0.20, f"PCR in balanced equilibrium band ({pcr:.2f}).")

    @staticmethod
    def sebi_peak_margin_headroom(available_margin: float, deployed_margin: float) -> float:
        """Returns headroom percentage remaining before reaching SEBI 85% PTRC cap."""
        if available_margin <= 0:
            return 0.0
        utilization = deployed_margin / available_margin
        return round(max(0.0, (0.85 - utilization) * 100.0), 2)

    @staticmethod
    def intraday_momentum_index(opens: np.ndarray, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray, period: int = 14) -> np.ndarray:
        """Intraday Momentum Index (IMI) combining RSI with candlestick body characteristics."""
        gains = np.where(closes > opens, closes - opens, 0.0)
        losses = np.where(closes < opens, opens - closes, 0.0)

        sum_gains = np.convolve(gains, np.ones(period), mode="same")
        sum_losses = np.convolve(losses, np.ones(period), mode="same")
        total = sum_gains + sum_losses

        return np.where(total > 0, (sum_gains / total) * 100.0, 50.0)

    @staticmethod
    def expiry_week_indicator(weekday: int, days_to_expiry: int) -> SignalResult:
        """
        Specialized 0DTE Indian Expiry Cycle Indicator.
        NSE/BSE runs expiries every weekday:
        0=MIDCPNIFTY (Mon), 1=FINNIFTY (Tue), 2=BANKNIFTY (Wed), 3=NIFTY50 (Thu), 4=SENSEX (Fri).
        """
        expiry_names = {0: "MIDCPNIFTY", 1: "FINNIFTY", 2: "BANKNIFTY", 3: "NIFTY50", 4: "SENSEX"}
        target_name = expiry_names.get(weekday, "NIFTY50")

        if days_to_expiry == 0:
            return SignalResult(1.0, "BUY", 0.90, f"0DTE Active for {target_name}. Extreme Theta decay & Gamma explosion opportunities.")
        elif days_to_expiry == 1:
            return SignalResult(0.5, "NEUTRAL", 0.60, f"1DTE for {target_name}. Position sequencing & margin netting critical.")
        else:
            return SignalResult(0.2, "NEUTRAL", 0.30, f"{days_to_expiry} days to {target_name} settlement. Trend-continuation focus.")
