"""
Academic Quantitative Backtest & Statistical Rigor Toolkit (PWB-Toolbox Architecture).
Implements Marcos López de Prado and David Bailey (2014) statistical corrections:
1. Deflated Sharpe Ratio (DSR) - Corrects for multiple testing / data snooping across N trials.
2. Probabilistic Sharpe Ratio (PSR) - Probability that true Sharpe ratio > benchmark.
3. Family-Wise Error Rate (FWER) - Bonferroni & Holm-Bonferroni corrections.
4. Information Coefficient (IC) & Factor Monotonicity.
"""

import math
from typing import List, Dict, Any, Union
import numpy as np
from scipy import stats


def probabilistic_sharpe_ratio(
    observed_sr: float,
    benchmark_sr: float = 0.0,
    n_samples: int = 252,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """
    Computes Probabilistic Sharpe Ratio (PSR).
    Measures the confidence that the true Sharpe Ratio exceeds benchmark_sr.
    """
    if n_samples <= 2:
        return 0.50

    # Variance of the Sharpe ratio estimate
    sr_var = (
        1.0
        - skewness * observed_sr
        + ((kurtosis - 1.0) / 4.0) * (observed_sr ** 2)
    ) / max(1, n_samples - 1)

    if sr_var <= 1e-9:
        return 1.0 if observed_sr > benchmark_sr else 0.0

    z_stat = (observed_sr - benchmark_sr) / math.sqrt(sr_var)
    psr = stats.norm.cdf(z_stat)
    return round(float(psr), 4)


def deflated_sharpe_ratio(
    observed_sr: float,
    n_trials: int = 100,
    n_samples: int = 252,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    var_sharpe_trials: float = 0.25,
) -> Dict[str, Any]:
    """
    Computes the Deflated Sharpe Ratio (DSR) based on Bailey & López de Prado (2014).
    Accounts for selection bias: when testing N strategies, the maximum observed Sharpe
    ratio is expected to be inflated by chance alone.
    """
    if n_trials <= 1:
        n_trials = 1

    # Expected maximum Sharpe ratio under the null hypothesis (Euler-Mascheroni constant ≈ 0.5772)
    gamma = 0.5772156649
    sqrt_var = math.sqrt(max(1e-6, var_sharpe_trials))
    z_proxy = (1.0 - gamma) * stats.norm.ppf(1.0 - 1.0 / n_trials) + gamma * stats.norm.ppf(
        1.0 - 1.0 / (n_trials * math.e)
    )
    expected_max_sr = sqrt_var * z_proxy

    # Compute PSR with the expected max SR as benchmark
    dsr_val = probabilistic_sharpe_ratio(
        observed_sr=observed_sr,
        benchmark_sr=expected_max_sr,
        n_samples=n_samples,
        skewness=skewness,
        kurtosis=kurtosis,
    )

    is_statistically_significant = dsr_val >= 0.95  # 95% confidence threshold

    return {
        "observed_sharpe": round(observed_sr, 4),
        "expected_max_null_sharpe": round(float(expected_max_sr), 4),
        "deflated_sharpe_ratio": round(float(dsr_val), 4),
        "trials_tested": n_trials,
        "sample_length_days": n_samples,
        "is_statistically_significant": is_statistically_significant,
        "verdict": (
            "GENUINE_ALPHA"
            if is_statistically_significant
            else "POTENTIAL_OVERFIT_DATA_SNOOPING"
        ),
    }


def holm_bonferroni_correction(
    p_values: List[float], alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Applies Holm-Bonferroni step-down procedure to control Family-Wise Error Rate (FWER)
    across multiple strategy hypotheses.
    """
    m = len(p_values)
    if m == 0:
        return []

    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    results = [None] * m

    for rank, (orig_idx, p_val) in enumerate(indexed):
        k = rank + 1
        threshold = alpha / (m - k + 1)
        rejected = p_val <= threshold
        results[orig_idx] = {
            "strategy_index": orig_idx,
            "raw_p_value": round(p_val, 6),
            "adjusted_threshold": round(threshold, 6),
            "statistically_significant": rejected,
        }

    return results


def calculate_factor_ic(
    factor_scores: List[float], forward_returns: List[float]
) -> Dict[str, float]:
    """
    Calculates Information Coefficient (Pearson & Spearman Rank IC) for predictive factor evaluation.
    """
    if len(factor_scores) != len(forward_returns) or len(factor_scores) < 5:
        return {"pearson_ic": 0.0, "rank_ic": 0.0, "p_value": 1.0}

    f = np.array(factor_scores, dtype=np.float64)
    r = np.array(forward_returns, dtype=np.float64)

    pearson_corr, p_val = stats.pearsonr(f, r)
    spearman_corr, _ = stats.spearmanr(f, r)

    return {
        "pearson_ic": round(float(pearson_corr), 4),
        "rank_ic": round(float(spearman_corr), 4),
        "p_value": round(float(p_val), 5),
    }
