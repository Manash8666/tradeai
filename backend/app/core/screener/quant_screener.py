import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import zoneinfo
import numpy as np

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


@dataclass
class ScreenerResult:
    ticker: str
    composite_score: float          # -1.0 to 1.0
    momentum_zscore: float          # Standardized momentum vs peers
    relative_strength_vs_nifty: float  # Alpha vs Nifty 50 (percentage points)
    liquidity_score: float          # 0.0 to 1.0 (higher = institutional grade liquidity)
    volatility_rank: float          # percentile rank (0=low vol, 1=high vol)
    oi_buildup_signal: str          # "LONG_BUILDUP" | "SHORT_BUILDUP" | "SHORT_COVERING" | "LONG_UNWINDING" | "NEUTRAL"
    india_vix_sensitivity: float    # Beta to India VIX
    rank: int                       # 1 = best setup
    recommendation: str             # "STRONG_BUY" | "BUY" | "WATCH" | "AVOID"
    rationale: str
    screened_at_ist: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NSEQuantScreener:
    """
    Institutional Cross-Sectional Screener for NSE 500 & F&O Universes.
    Evaluates statistical momentum Z-scores, relative alpha vs Nifty 50,
    microstructure liquidity depth, and derivatives Open Interest (OI) buildup dynamics.
    """

    def __init__(self):
        logger.info("[QUANT SCREENER] NSE/BSE Statistical Alpha Screener armed.")

    def screen_universe(self, tickers_data: List[Dict[str, Any]]) -> List[ScreenerResult]:
        """
        Processes a universe of tickers, computes cross-sectional Z-scores,
        and outputs an institutional rank-ordered selection.
        """
        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        if not tickers_data:
            return []

        # 1. Compute raw momentums for cross-sectional standardization
        raw_momentums = []
        for d in tickers_data:
            prices = d.get("prices_20d", [100.0] * 20)
            if len(prices) >= 2 and prices[0] > 0:
                mom = (prices[-1] - prices[0]) / prices[0]
            else:
                mom = 0.0
            raw_momentums.append(mom)

        mom_mean = float(np.mean(raw_momentums)) if raw_momentums else 0.0
        mom_std = float(np.std(raw_momentums)) if raw_momentums else 1.0
        if mom_std == 0:
            mom_std = 1.0

        intermediate_results = []

        # 2. Score individual assets
        for i, d in enumerate(tickers_data):
            ticker = d.get("ticker", f"STOCK_{i}")
            prices = d.get("prices_20d", [100.0] * 20)
            volumes = d.get("volumes_20d", [100000.0] * 20)
            nifty_prices = d.get("nifty_prices_20d", [24000.0] * 20)
            india_vix = float(d.get("india_vix", 14.5))
            current_oi = float(d.get("open_interest", 10000.0))
            prev_oi = float(d.get("prev_oi", 10000.0))

            # Momentum Z-Score
            raw_mom = raw_momentums[i]
            z_score = round(float((raw_mom - mom_mean) / mom_std), 2)

            # Relative Strength vs Nifty 50
            nifty_return = (nifty_prices[-1] - nifty_prices[0]) / max(1.0, nifty_prices[0]) if len(nifty_prices) >= 2 else 0.0
            rs_alpha = round(float((raw_mom - nifty_return) * 100.0), 2)  # Percentage points

            # Liquidity Score
            avg_vol = float(np.mean(volumes)) if volumes else 100000.0
            liquidity = round(float(np.clip(avg_vol / 1_000_000.0, 0.1, 1.0)), 2)

            # Volatility rank proxy
            price_vol = float(np.std(prices) / max(1.0, np.mean(prices))) if prices else 0.02
            vol_rank = round(float(np.clip(price_vol / 0.05, 0.0, 1.0)), 2)

            # Open Interest Buildup analysis
            price_chg = (prices[-1] - prices[-2]) / max(1.0, prices[-2]) if len(prices) >= 2 else 0.0
            oi_signal = self._detect_oi_signal(current_oi, prev_oi, price_chg)

            # Sensitivity to India VIX
            vix_sensitivity = round(float(0.5 + (vol_rank - 0.5) * 0.8), 2)

            # Composite Score (-1.0 to +1.0)
            composite = self._compute_composite_score(z_score, rs_alpha, liquidity, oi_signal)

            # Recommendation
            if composite >= 0.55 and liquidity >= 0.35:
                recommendation = "STRONG_BUY"
                rationale = f"Exceptional relative alpha (+{rs_alpha:.1f}% vs Nifty) confirmed by {oi_signal} and high liquidity."
            elif composite >= 0.20:
                recommendation = "BUY"
                rationale = f"Positive momentum Z-score ({z_score:+.1f}) with favorable technical positioning."
            elif composite <= -0.40:
                recommendation = "AVOID"
                rationale = f"Negative relative momentum and {oi_signal} distribution pressure."
            else:
                recommendation = "WATCH"
                rationale = "Consolidating without clear institutional edge."

            intermediate_results.append({
                "ticker": ticker,
                "composite_score": composite,
                "momentum_zscore": z_score,
                "relative_strength_vs_nifty": rs_alpha,
                "liquidity_score": liquidity,
                "volatility_rank": vol_rank,
                "oi_buildup_signal": oi_signal,
                "india_vix_sensitivity": vix_sensitivity,
                "recommendation": recommendation,
                "rationale": rationale,
            })

        # 3. Sort by composite score descending
        intermediate_results.sort(key=lambda x: x["composite_score"], reverse=True)

        final_results = []
        for rank, res in enumerate(intermediate_results, start=1):
            final_results.append(ScreenerResult(
                ticker=res["ticker"],
                composite_score=res["composite_score"],
                momentum_zscore=res["momentum_zscore"],
                relative_strength_vs_nifty=res["relative_strength_vs_nifty"],
                liquidity_score=res["liquidity_score"],
                volatility_rank=res["volatility_rank"],
                oi_buildup_signal=res["oi_buildup_signal"],
                india_vix_sensitivity=res["india_vix_sensitivity"],
                rank=rank,
                recommendation=res["recommendation"],
                rationale=res["rationale"],
                screened_at_ist=now_str,
            ))

        return final_results

    def _detect_oi_signal(self, current_oi: float, prev_oi: float, price_change_pct: float) -> str:
        """Categorizes Indian F&O Open Interest structure."""
        oi_change = current_oi - prev_oi
        oi_up = oi_change > 0
        price_up = price_change_pct > 0.001
        price_down = price_change_pct < -0.001

        if oi_up and price_up:
            return "LONG_BUILDUP"
        elif oi_up and price_down:
            return "SHORT_BUILDUP"
        elif not oi_up and price_up:
            return "SHORT_COVERING"
        elif not oi_up and price_down:
            return "LONG_UNWINDING"
        return "NEUTRAL"

    def _compute_composite_score(self, z_score: float, rs_alpha: float, liquidity: float, oi_signal: str) -> float:
        """Blends factors into unified confidence score."""
        oi_weights = {
            "LONG_BUILDUP": 1.0,
            "SHORT_COVERING": 0.5,
            "NEUTRAL": 0.0,
            "LONG_UNWINDING": -0.5,
            "SHORT_BUILDUP": -1.0,
        }
        oi_val = oi_weights.get(oi_signal, 0.0)

        # Standardize components
        z_norm = np.clip(z_score / 2.5, -1.0, 1.0)
        rs_norm = np.clip(rs_alpha / 10.0, -1.0, 1.0)
        liq_norm = (liquidity - 0.5) * 2.0  # -1.0 to 1.0

        composite = (z_norm * 0.35) + (rs_norm * 0.30) + (oi_val * 0.20) + (liq_norm * 0.15)
        return round(float(np.clip(composite, -1.0, 1.0)), 2)

    def get_nse_watchlist_alerts(self, results: List[ScreenerResult], threshold: float = 0.55) -> List[str]:
        """Extracts high-priority institutional setup alerts."""
        return [r.ticker for r in results if r.composite_score >= threshold]
