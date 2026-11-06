"""
Quantitative Mathematical Lab: Kou Jump-Diffusion & 0DTE Gamma Singularity Engine.

Rigorous mathematical formulation for:
1. Kou Double Exponential Jump-Diffusion Model:
   dS_t = (r - q - lambda * zeta) * S_t * dt + sigma * S_t * dW_t + (Y - 1) * S_t * dq_t
   where ln(Y) ~ DoubleExponential(p, eta_1, eta_2).
2. Dirac-Delta Gamma Singularity as tau -> 0+:
   lim_{tau -> 0+} Gamma(S, K, tau) = delta(S - K)
3. Higher-Order Taylor Series Greek Expansion:
   Delta P = Delta * dS + 0.5 * Gamma * (dS)^2 + (1/6) * Speed * (dS)^3 + Vanna * dS * dSigma + Theta * dt
4. 15x-20x (Rs. 2,000 -> Rs. 35,000+) 0DTE Payoff Probability & Expectancy Solver.
"""

import math
import random
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field


class TaylorExpansionResult(BaseModel):
    spot_change: float
    vol_change: float
    time_elapsed_hours: float
    delta_contribution: float
    gamma_contribution: float
    speed_contribution: float
    vanna_contribution: float
    theta_contribution: float
    total_estimated_pnl: float
    pct_return: float


class KouSimulationMetrics(BaseModel):
    initial_option_premium: float
    target_option_premium: float
    required_multiplier: float
    num_simulations: int
    success_count: int
    probability_of_17x_payoff: float
    expected_value_inr: float
    expected_edge_inr: float
    optimal_strike: float
    underlying_jump_threshold_points: float
    gamma_singularity_peak: float
    recommendation: str


def standard_normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def standard_normal_pdf(x: float) -> float:
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)


class GammaSingularityMathEngine:
    """
    Mathematical solver for 0DTE options dynamics and extreme payoff probability.
    """

    def compute_black_scholes_greeks(
        self,
        s: float,
        k: float,
        tau: float,
        r: float,
        sigma: float,
        is_call: bool = True,
    ) -> Dict[str, float]:
        """
        Computes Delta, Gamma, Speed, Theta, Vega, Vanna.
        tau in years.
        """
        tau = max(1e-6, tau)
        sigma = max(1e-4, sigma)
        sqrt_tau = math.sqrt(tau)

        d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * tau) / (sigma * sqrt_tau)
        d2 = d1 - sigma * sqrt_tau

        pdf_d1 = standard_normal_pdf(d1)
        cdf_d1 = standard_normal_cdf(d1)
        cdf_d2 = standard_normal_cdf(d2)

        if is_call:
            price = s * cdf_d1 - k * math.exp(-r * tau) * cdf_d2
            delta = cdf_d1
            theta = -(s * pdf_d1 * sigma) / (2.0 * sqrt_tau) - r * k * math.exp(-r * tau) * cdf_d2
        else:
            price = k * math.exp(-r * tau) * standard_normal_cdf(-d2) - s * standard_normal_cdf(-d1)
            delta = cdf_d1 - 1.0
            theta = -(s * pdf_d1 * sigma) / (2.0 * sqrt_tau) + r * k * math.exp(-r * tau) * standard_normal_cdf(-d2)

        gamma = pdf_d1 / (s * sigma * sqrt_tau)
        # Speed = dGamma / dS = - (Gamma / S) * (d1 / (sigma * sqrt_tau) + 1)
        speed = -(gamma / s) * (d1 / (sigma * sqrt_tau) + 1.0)
        # Vega in Rs per 1% vol = (S * sqrt(tau) * pdf(d1)) / 100
        vega = s * sqrt_tau * pdf_d1 / 100.0
        # Vanna = dDelta / dSigma = - pdf(d1) * d2 / sigma
        vanna = -pdf_d1 * d2 / sigma

        return {
            "price": max(0.05, price),
            "delta": delta,
            "gamma": gamma,
            "speed": speed,
            "theta_per_day": theta / 365.0,
            "vega": vega,
            "vanna": vanna,
        }

    def evaluate_taylor_expansion(
        self,
        s: float,
        k: float,
        tau_hours: float,
        sigma: float,
        ds: float,
        dsigma: float,
        dt_hours: float,
        is_call: bool = True,
        r: float = 0.065,
    ) -> TaylorExpansionResult:
        """
        4th-order Taylor expansion decomposition of option price change.
        """
        tau_years = tau_hours / (365.0 * 24.0)
        dt_years = dt_hours / (365.0 * 24.0)

        g = self.compute_black_scholes_greeks(s, k, tau_years, r, sigma, is_call)

        delta_term = g["delta"] * ds
        gamma_term = 0.5 * g["gamma"] * (ds ** 2)
        speed_term = (1.0 / 6.0) * g["speed"] * (ds ** 3)
        vanna_term = g["vanna"] * ds * dsigma
        theta_term = (g["theta_per_day"] * 365.0) * dt_years

        total_pnl = delta_term + gamma_term + speed_term + vanna_term + theta_term
        base_price = g["price"]
        pct = (total_pnl / max(0.01, base_price)) * 100.0

        return TaylorExpansionResult(
            spot_change=ds,
            vol_change=dsigma,
            time_elapsed_hours=dt_hours,
            delta_contribution=round(delta_term, 2),
            gamma_contribution=round(gamma_term, 2),
            speed_contribution=round(speed_term, 2),
            vanna_contribution=round(vanna_term, 2),
            theta_contribution=round(theta_term, 2),
            total_estimated_pnl=round(total_pnl, 2),
            pct_return=round(pct, 2),
        )

    def simulate_kou_0dte_payoff(
        self,
        spot: float = 24500.0,
        strike_otm: float = 24650.0,  # 150 pts OTM
        initial_premium: float = 20.0,  # Rs. 20 (Rs. 1,000 for 1 lot of 50, or Rs. 2,000 for 2 lots)
        target_multiplier: float = 17.5,  # 17.5x => Rs. 350 premium (Rs. 35,000 value on 2 lots)
        remaining_hours: float = 3.5,  # 0DTE midday
        sigma: float = 0.13,
        lambda_jump: float = 25.0,  # Expected jumps per year
        p_up: float = 0.40,  # Probability of positive jump
        eta_1: float = 30.0,  # Upward jump decay
        eta_2: float = 25.0,  # Downward jump decay
        num_sims: int = 10_000,
    ) -> KouSimulationMetrics:
        """
        Monte Carlo simulation of Kou Jump-Diffusion to evaluate exact probability of 15x-20x 0DTE explosion.
        """
        target_premium = initial_premium * target_multiplier
        r = 0.065
        dt = (remaining_hours / (365.0 * 24.0)) / 100.0  # 100 sub-steps
        total_time = remaining_hours / (365.0 * 24.0)

        # Kou jump expectation zeta
        zeta = (p_up * eta_1 / (eta_1 - 1.0)) + ((1.0 - p_up) * eta_2 / (eta_2 + 1.0)) - 1.0
        drift = (r - lambda_jump * zeta - 0.5 * sigma * sigma) * dt

        success_count = 0
        total_payoffs = 0.0
        steps = 100

        # Required spot for call to be worth target_premium at expiry:
        # P_T = max(0, S_T - K) >= target_premium => S_T >= K + target_premium
        # E.g. 24650 + 350 = 25000 (a 500 point move from 24500 = +2.04% intraday move in 3.5 hours)
        spot_trigger = strike_otm + target_premium

        for _ in range(num_sims):
            current_s = spot
            for _ in range(steps):
                # Diffusion increment
                z = random.gauss(0, 1)
                dw = math.sqrt(dt) * z

                # Poisson jump check
                jump_factor = 1.0
                if random.random() < (lambda_jump * dt):
                    # Jump occurred! Sample double exponential
                    if random.random() < p_up:
                        y_val = random.expovariate(eta_1)
                    else:
                        y_val = -random.expovariate(eta_2)
                    jump_factor = math.exp(y_val)

                current_s = current_s * math.exp(drift + sigma * dw) * jump_factor

            # Payoff at expiry
            terminal_intrinsic = max(0.0, current_s - strike_otm)
            if terminal_intrinsic >= target_premium:
                success_count += 1
            total_payoffs += terminal_intrinsic

        prob = success_count / num_sims
        # 2 lots of Nifty = 100 shares. Initial cost Rs. 2,000.
        avg_payoff_per_share = total_payoffs / num_sims
        expected_portfolio_pnl = (avg_payoff_per_share * 100.0) - (initial_premium * 100.0)

        # Gamma peak near expiry
        tau_final = 0.0001
        gamma_peak = standard_normal_pdf(0.0) / (strike_otm * sigma * math.sqrt(tau_final))

        rec = (
            "MATHEMATICALLY UNFAVORABLE: Negative statistical edge without a verified scheduled high-impact macro catalyst. "
            "Dirac-Delta gamma singularity requires spot to traverse into deep moneyness (S_T >= 25,000) before theta annihilation."
            if prob < 0.05
            else "CATALYTIC REGIME CONFIRMED: Jump probability exceeds hurdle threshold."
        )

        return KouSimulationMetrics(
            initial_option_premium=initial_premium,
            target_option_premium=target_premium,
            required_multiplier=target_multiplier,
            num_simulations=num_sims,
            success_count=success_count,
            probability_of_17x_payoff=round(prob, 4),
            expected_value_inr=round(avg_payoff_per_share * 100.0, 2),
            expected_edge_inr=round(expected_portfolio_pnl, 2),
            optimal_strike=strike_otm,
            underlying_jump_threshold_points=round(spot_trigger - spot, 2),
            gamma_singularity_peak=round(gamma_peak, 4),
            recommendation=rec,
        )


# Global instance
global_gamma_math = GammaSingularityMathEngine()
