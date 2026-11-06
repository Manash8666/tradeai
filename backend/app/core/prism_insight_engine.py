import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Tuple
import zoneinfo
import numpy as np

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


@dataclass
class PrismDecomposition:
    ticker: str
    total_return_pct: float

    # Return Attribution (Sum approximates total_return_pct)
    alpha_component: float       # Pure idiosyncratic skill / edge
    beta_component: float        # Broad Nifty 50 market exposure
    momentum_component: float    # Trend persistence contribution
    mean_reversion_component: float  # Mean-reversion swing contribution
    noise_component: float       # Unexplained residual

    # Risk Attribution
    vol_contribution: float      # Realized volatility contribution
    vix_sensitivity: float       # Sensitivity to India VIX shifts
    information_ratio: float     # Active return per unit of tracking error
    consistency_score: float     # Weekly winning percentage (0.0 to 1.0)

    insight_summary: str
    ist_generated: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PrismInsightEngine:
    """
    Multi-Dimensional Alpha Decomposition Engine (Prism Insight Framework).
    Decomposes realized and prospective P&L returns across orthogonal risk vectors:
    Alpha, Market Beta, Momentum, Mean-Reversion, and Volatility drag.
    """

    def __init__(self):
        logger.info("[PRISM INSIGHT] Multi-Factor Attribution Engine active.")

    def decompose_returns(
        self,
        ticker: str,
        daily_returns: List[float],
        nifty_returns: List[float],
        india_vix_series: Optional[List[float]] = None,
    ) -> PrismDecomposition:
        """
        Calculates orthogonal decomposition of asset returns vs Nifty benchmark.
        """
        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        ret_arr = np.asarray(daily_returns, dtype=float)
        nifty_arr = np.asarray(nifty_returns, dtype=float)

        min_len = min(len(ret_arr), len(nifty_arr))
        if min_len < 5:
            # Fallback for short histories
            return PrismDecomposition(
                ticker=ticker,
                total_return_pct=0.0,
                alpha_component=0.0,
                beta_component=0.0,
                momentum_component=0.0,
                mean_reversion_component=0.0,
                noise_component=0.0,
                vol_contribution=0.0,
                vix_sensitivity=0.0,
                information_ratio=0.0,
                consistency_score=0.5,
                insight_summary="Insufficient historical data for complete Prism decomposition.",
                ist_generated=now_str,
            )

        r = ret_arr[-min_len:]
        m = nifty_arr[-min_len:]
        total_ret = float(np.sum(r) * 100.0)

        # OLS Beta estimation
        cov_matrix = np.cov(r, m)
        var_market = cov_matrix[1, 1] if cov_matrix[1, 1] > 1e-8 else 1e-4
        beta = float(cov_matrix[0, 1] / var_market)

        # Beta component of total return
        beta_comp = float(beta * np.sum(m) * 100.0)

        # Active excess returns (residuals)
        residuals = r - beta * m
        alpha_comp = float(np.mean(residuals) * min_len * 100.0)

        # Autocorrelation of residuals to distinguish momentum vs mean-reversion
        if len(residuals) >= 3:
            autocorr = float(np.corrcoef(residuals[:-1], residuals[1:])[0, 1])
            if np.isnan(autocorr):
                autocorr = 0.0
        else:
            autocorr = 0.0

        if autocorr > 0.15:
            mom_comp = float(abs(alpha_comp) * min(0.6, autocorr))
            mr_comp = 0.0
        elif autocorr < -0.15:
            mr_comp = float(abs(alpha_comp) * min(0.6, abs(autocorr)))
            mom_comp = 0.0
        else:
            mom_comp = 0.0
            mr_comp = 0.0

        noise_comp = round(total_ret - (beta_comp + alpha_comp), 2)

        # Information Ratio (Annualized)
        tracking_error = float(np.std(residuals)) * np.sqrt(252.0)
        active_return_annual = float(np.mean(residuals)) * 252.0
        info_ratio = round(active_return_annual / max(1e-4, tracking_error), 2)

        # Realized volatility
        realized_vol = round(float(np.std(r) * np.sqrt(252.0) * 100.0), 1)

        # VIX Sensitivity
        if india_vix_series and len(india_vix_series) >= min_len:
            vix_arr = np.asarray(india_vix_series[-min_len:], dtype=float)
            vix_diff = np.diff(vix_arr)
            r_diff = r[1:]
            if len(vix_diff) >= 3 and np.std(vix_diff) > 0:
                vix_corr = float(np.corrcoef(r_diff, vix_diff)[0, 1])
                vix_sens = round(float(vix_corr), 2) if not np.isnan(vix_corr) else 0.0
            else:
                vix_sens = 0.0
        else:
            vix_sens = 0.0

        # Consistency score: % of positive return steps
        positive_steps = np.sum(r > 0)
        consistency = round(float(positive_steps / min_len), 2)

        # Synthesis
        if alpha_comp > beta_comp and alpha_comp > 0:
            summary = (
                f"[{ticker}] Strong proprietary alpha generation (+{alpha_comp:.1f}%). "
                f"Performance driven by genuine security selection rather than market tailwinds (Beta: {beta:.2f})."
            )
        elif beta_comp > 0:
            summary = (
                f"[{ticker}] Market-beta driven performance (+{beta_comp:.1f}%). "
                f"High sensitivity to Nifty 50 directional trajectory (Beta: {beta:.2f})."
            )
        else:
            summary = (
                f"[{ticker}] Defensive / negative active attribution. "
                f"Residual volatility ({realized_vol:.1f}%) dampening performance."
            )

        return PrismDecomposition(
            ticker=ticker,
            total_return_pct=round(total_ret, 2),
            alpha_component=round(alpha_comp, 2),
            beta_component=round(beta_comp, 2),
            momentum_component=round(mom_comp, 2),
            mean_reversion_component=round(mr_comp, 2),
            noise_component=noise_comp,
            vol_contribution=realized_vol,
            vix_sensitivity=vix_sens,
            information_ratio=info_ratio,
            consistency_score=consistency,
            insight_summary=summary,
            ist_generated=now_str,
        )

    def generate_portfolio_prism(self, positions: List[Dict[str, Any]], nifty_returns: List[float]) -> Dict[str, Any]:
        """
        Aggregates individual decompositions to reveal hidden factor concentrations across the portfolio.
        """
        if not positions:
            return {"status": "EMPTY", "message": "No active positions to decompose."}

        total_weight = sum(p.get("weight", 1.0) for p in positions)
        weighted_alpha = 0.0
        weighted_beta = 0.0
        decompositions = []

        for p in positions:
            ticker = p.get("ticker", "UNKNOWN")
            weight = p.get("weight", 1.0) / max(1e-5, total_weight)
            daily_rets = p.get("daily_returns", [0.01] * 20)

            decomp = self.decompose_returns(ticker, daily_rets, nifty_returns)
            decompositions.append(decomp)

            weighted_alpha += decomp.alpha_component * weight
            weighted_beta += decomp.beta_component * weight

        hidden_correlations = self.detect_hidden_correlations(positions)

        return {
            "portfolio_weighted_alpha": round(weighted_alpha, 2),
            "portfolio_weighted_beta": round(weighted_beta, 2),
            "decompositions": [d.to_dict() for d in decompositions],
            "hidden_correlations": hidden_correlations,
            "diversification_health": "OPTIMAL" if len(hidden_correlations) == 0 else "CONCENTRATION_WARNING",
        }

    def detect_hidden_correlations(self, positions: List[Dict[str, Any]], threshold: float = 0.70) -> List[Dict[str, Any]]:
        """
        Identifies pairs of positions with return correlation exceeding threshold (e.g. 0.70),
        warning the user of hidden systemic sector concentration.
        """
        pairs = []
        n = len(positions)
        for i in range(n):
            for j in range(i + 1, n):
                rets_i = positions[i].get("daily_returns", [])
                rets_j = positions[j].get("daily_returns", [])
                min_len = min(len(rets_i), len(rets_j))
                if min_len >= 5:
                    corr = float(np.corrcoef(rets_i[:min_len], rets_j[:min_len])[0, 1])
                    if not np.isnan(corr) and abs(corr) >= threshold:
                        pairs.append({
                            "ticker_a": positions[i].get("ticker"),
                            "ticker_b": positions[j].get("ticker"),
                            "correlation": round(corr, 2),
                            "risk_warning": f"Redundant exposure: {positions[i].get('ticker')} and {positions[j].get('ticker')} move synchronously ({corr:.2f}).",
                        })
        return pairs
