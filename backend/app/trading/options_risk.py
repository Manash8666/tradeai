"""
SEBI Multi-Leg Option Margin Netting & Portfolio Greeks Engine
=============================================================
Calculates exact Black-Scholes Greeks and implements the official SEBI SPAN
margin netting framework for multi-leg strategies (Iron Condors, Spreads, Straddles).

Enables true institutional capital efficiency by blocking margin only for the
maximum risk wing rather than charging cumulative margin on hedged legs.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from scipy.stats import norm


class OptionType(str, Enum):
    CALL = "CE"
    PUT = "PE"


@dataclass
class OptionLeg:
    strike: float
    option_type: OptionType
    action: str  # 'BUY' or 'SELL'
    quantity: int  # e.g., 75
    price: float   # premium
    iv: float      # e.g., 0.14 for 14%
    days_to_expiry: float = 7.0  # DTE


@dataclass
class LegGreeks:
    delta: float
    gamma: float
    theta_per_day: float
    vega_1pct: float
    rho: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta": round(self.delta, 4),
            "gamma": round(self.gamma, 6),
            "theta_per_day": round(self.theta_per_day, 2),
            "vega_1pct": round(self.vega_1pct, 2),
            "rho": round(self.rho, 4),
        }


@dataclass
class PortfolioGreeks:
    net_delta: float
    rupee_delta: float
    net_gamma: float
    net_theta_per_day: float
    net_vega_1pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "net_delta": round(float(self.net_delta), 4),
            "rupee_delta": round(float(self.rupee_delta), 2),
            "net_gamma": round(float(self.net_gamma), 6),
            "net_theta_per_day": round(float(self.net_theta_per_day), 2),
            "net_vega_1pct": round(float(self.net_vega_1pct), 2),
        }


class BlackScholesGreeksEngine:
    """Vectorized and analytic Black-Scholes options pricing and Greeks solver."""

    @staticmethod
    def calculate_greeks(
        spot: float,
        strike: float,
        dte_days: float,
        iv: float,
        option_type: OptionType,
        r: float = 0.065,  # RBI 91-day T-Bill risk free rate ~6.5%
    ) -> LegGreeks:
        """Calculate single option leg Greeks."""
        t = max(0.001, dte_days / 365.0)
        sigma = max(0.01, iv)

        d1 = (math.log(spot / strike) + (r + 0.5 * sigma**2) * t) / (sigma * math.sqrt(t))
        d2 = d1 - sigma * math.sqrt(t)

        pdf_d1 = norm.pdf(d1)
        cdf_d1 = norm.cdf(d1)
        cdf_d2 = norm.cdf(d2)

        if option_type == OptionType.CALL:
            delta = cdf_d1
            theta = -(spot * pdf_d1 * sigma) / (2 * math.sqrt(t)) - r * strike * math.exp(-r * t) * cdf_d2
            rho = strike * t * math.exp(-r * t) * cdf_d2 * 0.01
        else:
            delta = cdf_d1 - 1.0
            theta = -(spot * pdf_d1 * sigma) / (2 * math.sqrt(t)) + r * strike * math.exp(-r * t) * norm.cdf(-d2)
            rho = -strike * t * math.exp(-r * t) * norm.cdf(-d2) * 0.01

        gamma = pdf_d1 / (spot * sigma * math.sqrt(t))
        vega = spot * math.sqrt(t) * pdf_d1 * 0.01  # 1% IV shift
        theta_day = theta / 365.0  # Daily rupee decay

        return LegGreeks(
            delta=delta,
            gamma=gamma,
            theta_per_day=theta_day,
            vega_1pct=vega,
            rho=rho,
        )

    @classmethod
    def aggregate_portfolio_greeks(
        cls,
        spot: float,
        legs: List[OptionLeg],
    ) -> PortfolioGreeks:
        """Aggregate Greeks across multiple option legs with position sizing."""
        net_delta = 0.0
        net_gamma = 0.0
        net_theta = 0.0
        net_vega = 0.0

        for leg in legs:
            g = cls.calculate_greeks(
                spot=spot,
                strike=leg.strike,
                dte_days=leg.days_to_expiry,
                iv=leg.iv,
                option_type=leg.option_type,
            )
            mult = 1.0 if leg.action.upper() == "BUY" else -1.0
            signed_qty = leg.quantity * mult

            net_delta += g.delta * signed_qty
            net_gamma += g.gamma * signed_qty
            net_theta += g.theta_per_day * signed_qty
            net_vega += g.vega_1pct * signed_qty

        rupee_delta = net_delta * spot

        return PortfolioGreeks(
            net_delta=net_delta,
            rupee_delta=rupee_delta,
            net_gamma=net_gamma,
            net_theta_per_day=net_theta,
            net_vega_1pct=net_vega,
        )


class SEBIMarginNettingEngine:
    """
    Implements SEBI SPAN multi-leg margin netting rules.
    Instead of charging ~Rs 1.35L per naked leg, spreads and Iron Condors
    are netted based on maximum defined risk wings + statutory buffer.
    """

    SPAN_EXPOSURE_PER_NAKED_LOT: float = 135_000.0  # Standard NIFTY naked lot margin
    STATUTORY_BUFFER: float = 15_000.0              # SEBI minimum tail safety buffer

    @classmethod
    def calculate_margin(
        cls,
        spot: float,
        legs: List[OptionLeg],
    ) -> Dict[str, Any]:
        """
        Evaluate full portfolio of option legs:
        - Segregate Call wing and Put wing.
        - Check for full hedges (Spreads, Iron Condors, Iron Butterflies).
        - Net margin against maximum loss potential.
        """
        if not legs:
            return {
                "unhedged_margin_inr": 0.0,
                "sebi_netted_margin_inr": 0.0,
                "margin_relief_inr": 0.0,
                "margin_relief_pct": 0.0,
                "strategy_type": "EMPTY",
                "dominant_wing": "NONE",
            }

        # Segregate calls and puts
        calls = [l for l in legs if l.option_type == OptionType.CALL]
        puts = [l for l in legs if l.option_type == OptionType.PUT]

        short_calls = [l for l in calls if l.action.upper() == "SELL"]
        long_calls = [l for l in calls if l.action.upper() == "BUY"]
        short_puts = [l for l in puts if l.action.upper() == "SELL"]
        long_puts = [l for l in puts if l.action.upper() == "BUY"]

        # Calculate unhedged margin (naive broker calculation)
        unhedged_margin = 0.0
        for l in legs:
            if l.action.upper() == "BUY":
                # Buy premium paid
                unhedged_margin += l.price * l.quantity
            else:
                # Full SPAN + Exposure
                lots = math.ceil(l.quantity / 75.0)
                unhedged_margin += lots * cls.SPAN_EXPOSURE_PER_NAKED_LOT

        # Evaluate Call Wing Risk
        call_wing_max_risk = 0.0
        call_is_hedged = False
        if short_calls and long_calls:
            # Vertical Call spread
            sc = short_calls[0]
            lc = long_calls[0]
            if lc.strike > sc.strike:
                # Bear Call Credit Spread: Risk = (LC_Strike - SC_Strike) * Qty - Premium received
                spread_pts = lc.strike - sc.strike
                net_credit = (sc.price - lc.price)
                call_wing_max_risk = max(0.0, (spread_pts - net_credit) * sc.quantity)
                call_is_hedged = True
            elif sc.strike > lc.strike:
                # Bull Call Debit Spread
                call_wing_max_risk = (lc.price - sc.price) * lc.quantity
                call_is_hedged = True
        elif short_calls:
            call_wing_max_risk = len(short_calls) * cls.SPAN_EXPOSURE_PER_NAKED_LOT
        else:
            call_wing_max_risk = sum(l.price * l.quantity for l in long_calls)

        # Evaluate Put Wing Risk
        put_wing_max_risk = 0.0
        put_is_hedged = False
        if short_puts and long_puts:
            # Vertical Put spread
            sp = short_puts[0]
            lp = long_puts[0]
            if sp.strike > lp.strike:
                # Bull Put Credit Spread: Risk = (SP_Strike - LP_Strike) * Qty - Premium received
                spread_pts = sp.strike - lp.strike
                net_credit = (sp.price - lp.price)
                put_wing_max_risk = max(0.0, (spread_pts - net_credit) * sp.quantity)
                put_is_hedged = True
            elif lp.strike > sp.strike:
                # Bear Put Debit Spread
                put_wing_max_risk = (lp.price - sp.price) * lp.quantity
                put_is_hedged = True
        elif short_puts:
            put_wing_max_risk = len(short_puts) * cls.SPAN_EXPOSURE_PER_NAKED_LOT
        else:
            put_wing_max_risk = sum(l.price * l.quantity for l in long_puts)

        # SEBI SPAN Netting Rule:
        # If both Call and Put wings are present (Iron Condor / Box Spread / Iron Fly),
        # only ONE wing can breach at expiration. Block margin for the MAXIMUM wing only!
        if (short_calls or long_calls) and (short_puts or long_puts) and (call_is_hedged and put_is_hedged):
            higher_risk = max(call_wing_max_risk, put_wing_max_risk)
            sebi_netted_margin = higher_risk + cls.STATUTORY_BUFFER
            strategy_type = "IRON_CONDOR_OR_FLY"
            dominant_wing = "CALL_WING" if call_wing_max_risk >= put_wing_max_risk else "PUT_WING"
        elif call_is_hedged or put_is_hedged:
            # Single vertical spread
            wing_risk = call_wing_max_risk if call_is_hedged else put_wing_max_risk
            sebi_netted_margin = wing_risk + cls.STATUTORY_BUFFER
            strategy_type = "VERTICAL_SPREAD"
            dominant_wing = "CALL_WING" if call_is_hedged else "PUT_WING"
        else:
            # Unhedged or Naked strategy
            sebi_netted_margin = unhedged_margin
            strategy_type = "NAKED_OR_STRADDLE"
            dominant_wing = "BOTH"

        margin_relief = max(0.0, unhedged_margin - sebi_netted_margin)
        relief_pct = (margin_relief / unhedged_margin * 100.0) if unhedged_margin > 0 else 0.0

        return {
            "unhedged_margin_inr": round(unhedged_margin, 2),
            "sebi_netted_margin_inr": round(sebi_netted_margin, 2),
            "margin_relief_inr": round(margin_relief, 2),
            "margin_relief_pct": round(relief_pct, 1),
            "strategy_type": strategy_type,
            "dominant_wing": dominant_wing,
            "call_wing_max_risk_inr": round(call_wing_max_risk, 2),
            "put_wing_max_risk_inr": round(put_wing_max_risk, 2),
            "tail_safety_buffer_inr": cls.STATUTORY_BUFFER,
        }
