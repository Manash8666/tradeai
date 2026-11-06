"""
Hagan et al. (2002) SABR Volatility Surface Recalibration Pipeline
==================================================================
Fits the stochastic volatility SABR model:
    dF_t = alpha_t * F_t^beta * dW_1,t
    d alpha_t = nu * alpha_t * dW_2,t
    dW_1,t * dW_2,t = rho * dt

With fixed beta = 0.5 (standard square-root smile backbone for Indian Index Options).
Solves for alpha (ATM vol), rho (skew correlation), and nu (vol of vol) using L-BFGS-B.

Generates a continuous 3D volatility surface mesh (Strike x DTE x Implied Volatility).
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import numpy as np
from scipy.optimize import minimize


@dataclass
class SABRParameters:
    alpha: float  # ATM Volatility level
    beta: float   # Elasticity exponent (fixed 0.5 for Nifty)
    rho: float    # Correlation (negative skew)
    nu: float     # Vol-of-vol

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": round(self.alpha, 4),
            "beta": round(self.beta, 2),
            "rho": round(self.rho, 4),
            "nu": round(self.nu, 4),
        }


class SABRCalibrator:
    """Hagan SABR Volatility surface calibrator and 3D mesh generator."""

    def __init__(self, beta: float = 0.5):
        self.beta = beta

    def sabr_implied_vol(
        self,
        strike: float,
        forward: float,
        t: float,
        alpha: float,
        rho: float,
        nu: float,
    ) -> float:
        """Evaluate Hagan's expansion formula for Black implied volatility."""
        if strike <= 0 or forward <= 0 or t <= 0:
            return alpha

        # Ensure stability bounds
        alpha = max(0.001, alpha)
        nu = max(0.001, nu)
        rho = max(-0.999, min(0.999, rho))
        beta = self.beta

        fk = forward * strike
        log_fk = math.log(forward / strike)

        # ATM check
        if abs(forward - strike) < 1e-4:
            f_term = forward ** (1.0 - beta)
            term1 = alpha / f_term
            bracket = (
                ((1.0 - beta) ** 2 / 24.0) * (alpha**2 / (forward ** (2.0 - 2.0 * beta)))
                + (0.25 * rho * beta * nu * alpha / f_term)
                + ((2.0 - 3.0 * rho**2) / 24.0) * (nu**2)
            )
            return term1 * (1.0 + bracket * t)

        # Away from ATM
        fk_term = fk ** ((1.0 - beta) / 2.0)
        z = (nu / alpha) * fk_term * log_fk

        # x(z) calculation
        sqrt_term = math.sqrt(max(0.0, 1.0 - 2.0 * rho * z + z**2))
        num = sqrt_term + z - rho
        den = 1.0 - rho
        if num <= 0 or den <= 0:
            return alpha
        xz = math.log(num / den)

        if abs(xz) < 1e-7:
            z_over_xz = 1.0
        else:
            z_over_xz = z / xz

        denom = fk_term * (
            1.0
            + ((1.0 - beta) ** 2 / 24.0) * (log_fk**2)
            + ((1.0 - beta) ** 4 / 1920.0) * (log_fk**4)
        )

        bracket = (
            ((1.0 - beta) ** 2 / 24.0) * (alpha**2 / (fk ** (1.0 - beta)))
            + (0.25 * rho * beta * nu * alpha / fk_term)
            + ((2.0 - 3.0 * rho**2) / 24.0) * (nu**2)
        )

        vol = (alpha / denom) * z_over_xz * (1.0 + bracket * t)
        return max(0.02, min(2.5, vol))

    def calibrate(
        self,
        strikes: List[float],
        market_ivs: List[float],
        forward: float,
        dte_days: float,
    ) -> SABRParameters:
        """Calibrate alpha, rho, nu to market strike IV smile using L-BFGS-B."""
        t = max(0.001, dte_days / 365.0)

        # Objective function: Mean Squared Error
        def objective(params):
            alpha, rho, nu = params
            total_err = 0.0
            for k, mkt_iv in zip(strikes, market_ivs):
                model_iv = self.sabr_implied_vol(k, forward, t, alpha, rho, nu)
                total_err += (model_iv - mkt_iv) ** 2
            return total_err / len(strikes)

        # Initial parameter estimates
        init_alpha = np.mean(market_ivs)
        init_rho = -0.45  # typical Indian index skew
        init_nu = 0.85    # typical index vol-of-vol

        bounds = [
            (0.01, 1.0),    # alpha
            (-0.95, 0.95),  # rho
            (0.05, 3.0),    # nu
        ]

        res = minimize(
            objective,
            [init_alpha, init_rho, init_nu],
            method="L-BFGS-B",
            bounds=bounds,
        )

        opt_alpha, opt_rho, opt_nu = res.x
        return SABRParameters(alpha=opt_alpha, beta=self.beta, rho=opt_rho, nu=opt_nu)

    def generate_3d_surface(
        self,
        forward: float = 23800.0,
        base_iv: float = 0.138,
    ) -> Dict[str, Any]:
        """
        Generate a complete 3D volatility surface across strikes and expiration tenors.
        Returns grid of (strike, dte, vol) vertices for WebGL / Three.js rendering.
        """
        # Tenors: 1d, 7d, 14d, 21d, 30d, 45d, 60d
        dtes = [1.0, 7.0, 14.0, 21.0, 30.0, 45.0, 60.0]
        # Strikes: 21 strikes spanning -6% to +6% around forward
        strike_pcts = np.linspace(0.94, 1.06, 21)
        strikes = [round(forward * p, 0) for p in strike_pcts]

        # Representative calibration parameters
        params = SABRParameters(alpha=base_iv, beta=self.beta, rho=-0.48, nu=0.92)

        surface_grid: List[Dict[str, Any]] = []
        matrix: List[List[float]] = []

        for dte in dtes:
            t = dte / 365.0
            row = []
            for k in strikes:
                vol = self.sabr_implied_vol(k, forward, t, params.alpha, params.rho, params.nu)
                vol_pct = round(vol * 100.0, 2)
                row.append(vol_pct)
                surface_grid.append({
                    "strike": k,
                    "dte": dte,
                    "iv_pct": vol_pct,
                    "moneyness": round(k / forward, 3),
                })
            matrix.append(row)

        return {
            "forward": forward,
            "calibrated_params": params.to_dict(),
            "dtes": dtes,
            "strikes": strikes,
            "matrix": matrix,
            "surface_points_count": len(surface_grid),
            "sample_points": surface_grid,
        }


# Global singleton calibrator
sabr_calibrator = SABRCalibrator()
