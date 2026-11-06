import logging
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class RegimeDefinition:
    regime: str
    max_position_size_pct: float
    preferred_strategy_type: str
    risk_multiplier: float
    description: str


class IndiaVIXRegimeRouter:
    """
    Volatility Regime Router engineered specifically for the Indian Market (India VIX).
    Maps current volatility state to permissible position sizes and tactical strategy modes.
    """

    def __init__(self):
        logger.info("[REGIME ROUTER] India VIX Dynamic Allocation Gateway armed.")

    def get_regime(self, india_vix: float) -> Dict[str, Any]:
        """
        Calculates the active volatility regime and risk parameters based on India VIX.
        """
        if india_vix < 13.0:
            regime = RegimeDefinition(
                regime="ULTRA_LOW_VOL",
                max_position_size_pct=15.0,
                preferred_strategy_type="MOMENTUM_BREAKOUT",
                risk_multiplier=1.25,
                description="Complementary low option premiums; aggressive directional momentum favorable.",
            )
        elif 13.0 <= india_vix < 18.0:
            regime = RegimeDefinition(
                regime="LOW_VOL_NORMAL",
                max_position_size_pct=10.0,
                preferred_strategy_type="TREND_FOLLOWING_OPTION_WRITING",
                risk_multiplier=1.00,
                description="Optimal Indian market equilibrium; standard institutional theta/delta models active.",
            )
        elif 18.0 <= india_vix < 22.0:
            regime = RegimeDefinition(
                regime="MEDIUM_VOL_ELEVATED",
                max_position_size_pct=6.0,
                preferred_strategy_type="DELTA_NEUTRAL_STRANGLES",
                risk_multiplier=0.70,
                description="Elevated uncertainty; enforce strict sizing and mandatory stop-losses.",
            )
        elif 22.0 <= india_vix < 28.0:
            regime = RegimeDefinition(
                regime="HIGH_VOL_TURBULENT",
                max_position_size_pct=3.5,
                preferred_strategy_type="DEFENSIVE_PUT_HEDGES",
                risk_multiplier=0.40,
                description="Severe market turbulence; directional trades restrained, options restricted to hedging.",
            )
        else:
            regime = RegimeDefinition(
                regime="EXTREME_VOL_CRISIS",
                max_position_size_pct=0.0,
                preferred_strategy_type="CAPITAL_PRESERVATION_HALT",
                risk_multiplier=0.00,
                description="Crisis volatility (VIX >= 28.0); all directional allocations halted.",
            )

        return {
            "india_vix": india_vix,
            "regime": regime.regime,
            "max_position_size_pct": regime.max_position_size_pct,
            "preferred_strategy_type": regime.preferred_strategy_type,
            "risk_multiplier": regime.risk_multiplier,
            "description": regime.description,
            "should_hedge": self.should_use_options_hedge(india_vix),
        }

    def get_position_size_multiplier(self, india_vix: float, base_size: float = 1.0) -> float:
        """Scales position size smoothly with volatility dampening."""
        regime_info = self.get_regime(india_vix)
        return round(base_size * regime_info["risk_multiplier"], 3)

    def should_use_options_hedge(self, india_vix: float) -> bool:
        """Mandatory options hedging threshold for the Indian derivative books."""
        return india_vix >= 18.0


class HarvardFactorModel:
    """
    Five-Factor Quantitative Alpha Model adapted for Indian Equity & F&O Universes.
    Balances Momentum, Quality, Value, Size, and Microstructure Liquidity.
    """

    def __init__(self):
        # Base factor allocation
        self.weights = {
            "momentum": 0.30,
            "quality": 0.20,
            "value": 0.20,
            "size": 0.15,
            "liquidity": 0.15,
        }
        self.nifty_pe_baseline = 21.5

    def score_asset(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes composite multi-factor score (-1.0 to +1.0) for an NSE ticker.
        """
        ticker = market_data.get("ticker", "UNKNOWN")
        is_psu = market_data.get("is_psu", False)
        is_nifty50 = market_data.get("is_nifty50", True)

        # 1. Momentum: 20-day price change
        mom_20d = float(market_data.get("momentum_20d_pct", 0.05))
        mom_score = np.clip(mom_20d / 0.10, -1.0, 1.0)
        if is_nifty50:
            mom_score *= 1.1  # Nifty 50 momentum persistence is empirically stronger

        # 2. Quality: Price stability / low historical variance
        volatility_annual = float(market_data.get("historical_volatility", 0.22))
        quality_score = np.clip((0.30 - volatility_annual) / 0.15, -1.0, 1.0)

        # 3. Value: PE vs Nifty baseline
        pe_ratio = float(market_data.get("pe_ratio", 21.5))
        value_score = np.clip((self.nifty_pe_baseline - pe_ratio) / 10.0, -1.0, 1.0)
        # Indian PSU adjustment: PE is structurally lower in PSU sector
        if is_psu:
            value_weight_factor = 0.5
        else:
            value_weight_factor = 1.0

        # 4. Size: Market Cap rank
        is_large_cap = is_nifty50 or market_data.get("market_cap_tier") == "LARGE"
        size_score = 0.6 if is_large_cap else 0.1

        # 5. Liquidity: Volume vs 20d Average
        volume_surge = float(market_data.get("volume_surge", 1.0))
        liquidity_score = np.clip((volume_surge - 1.0) / 1.5, -0.5, 1.0)

        # Adjusted factor weight calculation
        w_mom = self.weights["momentum"]
        w_qual = self.weights["quality"]
        w_val = self.weights["value"] * value_weight_factor
        w_size = self.weights["size"]
        w_liq = self.weights["liquidity"]
        total_w = w_mom + w_qual + w_val + w_size + w_liq

        composite_score = round(
            (
                mom_score * w_mom
                + quality_score * w_qual
                + value_score * w_val
                + size_score * w_size
                + liquidity_score * w_liq
            )
            / total_w,
            3,
        )

        return {
            "ticker": ticker,
            "composite_score": composite_score,
            "factor_scores": {
                "momentum": round(float(mom_score), 3),
                "quality": round(float(quality_score), 3),
                "value": round(float(value_score), 3),
                "size": round(float(size_score), 3),
                "liquidity": round(float(liquidity_score), 3),
            },
            "verdict": "STRONG_FACTOR_SUPPORT" if composite_score > 0.4 else ("FACTOR_HEADWIND" if composite_score < -0.3 else "NEUTRAL"),
        }
