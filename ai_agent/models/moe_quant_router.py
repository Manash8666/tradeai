"""
Mixture-of-Experts (MoE) Quantitative Signal Router.
Inspired by DeepSeek-V3's Multi-Head Latent Attention (MLA) and DeepSeekMoE routing architecture.

Routes market conditions across 4 specialized expert models:
1. MacroRegimeExpert: Global yields, Brent crude, DXY, GIFT Nifty.
2. DerivativesGreekExpert: Option chain smile, skew, Delta/Gamma imbalances.
3. PriceActionSMCExpert: Fair Value Gaps (FVG), Order Blocks (OB), Break of Structure (BOS).
4. ExecutionRiskExpert: PTRC limits, margin capacity, Greed Lock circuit breaker.

Calculates Top-2 Softmax routing weights to form a high-conviction quantitative directive.
"""

import math
from typing import Dict, Any, List, Tuple
import numpy as np


class MacroRegimeExpert:
    """Expert 1: Evaluates macroeconomic and Dalal Street intermarket transmission."""

    def evaluate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        crude = market_data.get("brent_crude_usd", 80.0)
        gift_spread = market_data.get("gift_nifty_spread", 25.0)
        dxy = market_data.get("dxy_index", 103.5)

        # Indian market is inversely related to crude surges and strong DXY
        macro_score = (gift_spread * 1.5) - (max(0.0, crude - 80.0) * 8.0) - (max(0.0, dxy - 104.0) * 15.0)
        prob_bullish = 1.0 / (1.0 + math.exp(-macro_score / 30.0))

        return {
            "expert_name": "MacroRegimeExpert",
            "score": round(macro_score, 2),
            "bias": "BULLISH" if prob_bullish > 0.55 else ("BEARISH" if prob_bullish < 0.45 else "NEUTRAL"),
            "confidence": round(float(abs(prob_bullish - 0.5) * 2.0), 3),
            "key_driver": f"GIFT Nifty spread (+{gift_spread} pts) vs Brent Crude (${crude})",
        }


class DerivativesGreekExpert:
    """Expert 2: Evaluates option surface skew, Implied Volatility smile, and Gamma imbalances."""

    def evaluate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        atm_iv = market_data.get("atm_iv", 15.8)
        pcr = market_data.get("pcr", 1.05)
        skew = market_data.get("volatility_skew", 0.0)

        # PCR > 1.2 is bullish institutional put writing; Skew > 0 reflects downside hedging demand
        greek_score = (pcr - 1.0) * 50.0 - (skew * 10.0)
        prob_bullish = 1.0 / (1.0 + math.exp(-greek_score / 25.0))

        return {
            "expert_name": "DerivativesGreekExpert",
            "score": round(greek_score, 2),
            "bias": "BULLISH" if prob_bullish > 0.55 else ("BEARISH" if prob_bullish < 0.45 else "NEUTRAL"),
            "confidence": round(float(abs(prob_bullish - 0.5) * 2.0), 3),
            "key_driver": f"PCR OI ({pcr}) with ATM IV at {atm_iv}%",
        }


class PriceActionSMCExpert:
    """Expert 3: Evaluates Fair Value Gaps, Order Blocks, and structural break of pivots."""

    def evaluate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        active_bull_fvgs = market_data.get("bull_fvgs_count", 2)
        active_bear_fvgs = market_data.get("bear_fvgs_count", 1)
        bos_bullish = market_data.get("bos_bullish_count", 3)

        smc_score = (active_bull_fvgs * 15.0) - (active_bear_fvgs * 15.0) + (bos_bullish * 10.0)
        prob_bullish = 1.0 / (1.0 + math.exp(-smc_score / 35.0))

        return {
            "expert_name": "PriceActionSMCExpert",
            "score": round(smc_score, 2),
            "bias": "BULLISH" if prob_bullish > 0.55 else ("BEARISH" if prob_bullish < 0.45 else "NEUTRAL"),
            "confidence": round(float(abs(prob_bullish - 0.5) * 2.0), 3),
            "key_driver": f"Bullish FVGs ({active_bull_fvgs}) & BOS ({bos_bullish}) dominance",
        }


class ExecutionRiskExpert:
    """Expert 4: Enforces pre-trade capital exposure, drawdowns, and Greed Lock limits."""

    def evaluate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        margin_used_pct = market_data.get("margin_used_pct", 18.5)
        greed_locked = market_data.get("greed_locked", False)
        daily_loss_pct = market_data.get("daily_loss_pct", 0.4)

        risk_score = 50.0 - (margin_used_pct * 1.5) - (daily_loss_pct * 40.0)
        if greed_locked:
            risk_score = -100.0

        is_safe = risk_score > 0 and not greed_locked

        return {
            "expert_name": "ExecutionRiskExpert",
            "score": round(risk_score, 2),
            "bias": "EXECUTION_PERMITTED" if is_safe else "EXECUTION_BLOCKED",
            "confidence": 0.98 if greed_locked else 0.85,
            "key_driver": "Greed Lock Active" if greed_locked else f"Margin at {margin_used_pct}% (Capacity OK)",
        }


class IndianMarketMoERouter:
    """
    Top-2 Sparse Mixture-of-Experts Gating Router for Indian Market Quantitative Alpha.
    """

    def __init__(self):
        self.experts = {
            "MacroRegime": MacroRegimeExpert(),
            "DerivativesGreek": DerivativesGreekExpert(),
            "PriceActionSMC": PriceActionSMCExpert(),
            "ExecutionRisk": ExecutionRiskExpert(),
        }

    def route_and_infer(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs all experts, computes routing softmax weights, and selects Top-2 experts.
        """
        evaluations = {}
        scores = []
        names = list(self.experts.keys())

        for name, expert in self.experts.items():
            ev = expert.evaluate(market_data)
            evaluations[name] = ev
            scores.append(abs(ev["score"]) * ev["confidence"])

        # Softmax over expert scores
        scores_arr = np.array(scores, dtype=np.float64)
        exp_scores = np.exp(scores_arr - np.max(scores_arr))
        softmax_weights = exp_scores / np.sum(exp_scores)

        # Select Top-2 Experts
        top_2_indices = np.argsort(softmax_weights)[::-1][:2]
        top_experts = [
            {
                "expert": names[idx],
                "weight_pct": round(float(softmax_weights[idx]) * 100.0, 1),
                "evaluation": evaluations[names[idx]],
            }
            for idx in top_2_indices
        ]

        # Consolidated Alpha Directive
        risk_evaluation = evaluations["ExecutionRisk"]
        primary_expert = top_experts[0]["evaluation"]

        if risk_evaluation["bias"] == "EXECUTION_BLOCKED":
            consolidated_bias = "RISK_LOCKOUT"
            action_directive = "FLATTEN_OR_STAND_ASIDE"
        else:
            consolidated_bias = primary_expert["bias"]
            action_directive = (
                "AGGRESSIVE_CALL_SPREAD_OR_LONG"
                if consolidated_bias == "BULLISH"
                else ("DEFENSIVE_PUT_SPREAD_OR_HEDGE" if consolidated_bias == "BEARISH" else "NEUTRAL_IRON_CONDOR")
            )

        return {
            "top_2_experts": top_experts,
            "routing_weights": {names[i]: round(float(softmax_weights[i]) * 100.0, 1) for i in range(len(names))},
            "consolidated_bias": consolidated_bias,
            "action_directive": action_directive,
            "risk_guard": risk_evaluation["bias"],
            "architecture": "DeepSeek-V3 Sparse MoE (Top-2 Gating)",
        }


moe_quant_router = IndianMarketMoERouter()
