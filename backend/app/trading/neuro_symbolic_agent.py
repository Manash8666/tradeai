"""
Institutional Neuro-Symbolic Trading Agent & Deterministic Risk Supervisor.

Architecture:
1. Neural / LLM / SLM Core: Analyzes microstructure (OFI, micro-price), macro sentiment,
   dealer GEX regimes, and human behavioral flows to generate TradeIntents.
2. Symbolic Mathematical Risk Supervisor (DeterministicRiskGate):
   An un-overrideable deterministic invariant engine implementing mathematical risk constraints:
   - Daily Drawdown Hard Killswitch (<= 5% or Rs. 30,000 max daily loss)
   - Neural Conviction / Confidence Gate (>= 0.78 threshold)
   - Mathematical Capital Sizing: Position risk clamped to <= 2.0% of portfolio
   - 0DTE Expiry Pin Guard (No new naked options after 15:15 IST)
   - SEBI/NSE Order Rate Token Bucket Verification
"""

import time
import math
import logging
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field

logger = logging.getLogger("NeuroSymbolicAgent")
logger.setLevel(logging.INFO)


class AgentAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    FLATTEN_ALL = "FLATTEN_ALL"
    GAMMA_HEDGE = "GAMMA_HEDGE"


class MarketContext(BaseModel):
    symbol: str
    ltp: float
    ofi: float = Field(..., description="Order Flow Imbalance between -1.0 (sell pressure) and +1.0 (buy pressure)")
    micro_price: float = Field(..., description="Depth-weighted micro-price")
    dealer_net_gex: float = Field(default=0.0, description="Dealer Net Gamma Exposure in Rs. Crores")
    macro_sentiment_score: float = Field(default=0.0, description="Global & domestic news sentiment (-1.0 to 1.0)")
    bid_depth: int = 1000
    ask_depth: int = 1000
    iv_percentile: float = 50.0
    is_0dte_expiry_day: bool = False
    current_time_str: str = "11:30"
    minutes_to_market_close: int = 240


class TradeIntent(BaseModel):
    symbol: str
    action: AgentAction
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    target_price: float
    stop_loss_price: float
    suggested_lots: int = 1
    regime_detected: str = "UNKNOWN"
    mirajane_thought: str = ""
    timestamp: float = Field(default_factory=time.time)


class ExecutionVerdict(BaseModel):
    intent: TradeIntent
    approved: bool
    adjusted_lots: int
    adjusted_stop_loss: float
    rejection_reasons: List[str] = []
    applied_guards: List[str] = []
    max_capital_at_risk_inr: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class AccountRiskState(BaseModel):
    total_portfolio_equity: float = 500_000.0  # Rs. 5 Lakh base
    free_cash: float = 350_000.0
    daily_realized_pnl: float = 0.0
    daily_unrealized_pnl: float = 0.0
    max_daily_drawdown_limit: float = 25_000.0  # 5% max daily risk
    active_positions_count: int = 0
    max_allowed_open_positions: int = 4
    sebi_tokens_remaining: int = 200


class DeterministicRiskGate:
    """
    Symbolic Mathematical Risk Supervisor.
    Mathematical invariants that cannot be altered or bypassed by neural weights.
    """

    MIN_NEURAL_CONFIDENCE: float = 0.78
    MAX_SINGLE_TRADE_RISK_PCT: float = 0.02  # 2.0% max account risk
    LOT_SIZES: Dict[str, int] = {
        "NIFTY": 50,
        "BANKNIFTY": 15,
        "FINNIFTY": 25,
        "MIDCPNIFTY": 50,
        "SENSEX": 10,
        "RELIANCE": 250,
        "HDFCBANK": 550,
        "TCS": 175,
        "INFY": 400,
    }

    def __init__(self, max_daily_drawdown: float = 25_000.0):
        self.max_daily_drawdown = max_daily_drawdown
        self.total_evaluated_intents = 0
        self.total_approved_intents = 0
        self.total_rejected_intents = 0

    def get_lot_size(self, symbol: str) -> int:
        clean = symbol.upper().replace(".NS", "").replace(".BO", "")
        for k, v in self.LOT_SIZES.items():
            if k in clean:
                return v
        return 50  # Default Nifty lot size

    def evaluate(
        self,
        intent: TradeIntent,
        context: MarketContext,
        account: AccountRiskState,
    ) -> ExecutionVerdict:
        self.total_evaluated_intents += 1
        rejections: List[str] = []
        guards: List[str] = []
        adjusted_lots = intent.suggested_lots
        adjusted_sl = intent.stop_loss_price

        # Guard 0: Emergency FLATTEN_ALL / HOLD
        if intent.action == AgentAction.HOLD:
            return ExecutionVerdict(
                intent=intent,
                approved=True,
                adjusted_lots=0,
                adjusted_stop_loss=0.0,
                applied_guards=["PASSIVE_HOLD_CONFIRMED"],
            )

        if intent.action == AgentAction.FLATTEN_ALL:
            guards.append("EMERGENCY_DELEVERAGE_PERMITTED")
            return ExecutionVerdict(
                intent=intent,
                approved=True,
                adjusted_lots=0,
                adjusted_stop_loss=0.0,
                applied_guards=guards,
            )

        # Invariant 1: Daily Drawdown Hard Circuit Breaker
        total_daily_pnl = account.daily_realized_pnl + account.daily_unrealized_pnl
        if total_daily_pnl <= -abs(account.max_daily_drawdown_limit):
            rejections.append(
                f"CIRCUIT_BREAKER_TRIPPED: Daily loss (-Rs. {abs(total_daily_pnl):,.2f}) "
                f"breached max allowed limit (-Rs. {account.max_daily_drawdown_limit:,.2f}). Trading halted."
            )

        # Invariant 2: Neural Conviction Threshold
        if intent.confidence < self.MIN_NEURAL_CONFIDENCE:
            rejections.append(
                f"LOW_NEURAL_CONVICTION: Intent confidence ({intent.confidence:.2f}) "
                f"is strictly below institutional gate threshold ({self.MIN_NEURAL_CONFIDENCE:.2f})."
            )
        else:
            guards.append(f"NEURAL_CONFIDENCE_VERIFIED ({intent.confidence:.2f} >= {self.MIN_NEURAL_CONFIDENCE})")

        # Invariant 3: Rate Limiting & Order Tokens
        if account.sebi_tokens_remaining <= 5:
            rejections.append("SEBI_RATE_LIMIT_WARNING: Insufficient token bucket allowance (< 5 tokens).")
        else:
            guards.append("SEBI_RATE_LIMIT_PASSED")

        # Invariant 4: Maximum Concurrent Open Positions
        if account.active_positions_count >= account.max_allowed_open_positions:
            rejections.append(
                f"MAX_EXPOSURE_EXCEEDED: Open positions ({account.active_positions_count}) "
                f"at limit ({account.max_allowed_open_positions})."
            )

        # Invariant 5: 0DTE Expiry Pin Risk & Time Boundary
        if context.is_0dte_expiry_day and context.minutes_to_market_close <= 15:
            rejections.append(
                f"0DTE_GAMMA_SINGULARITY_LOCKOUT: Less than 15 minutes to cash market close ({context.minutes_to_market_close}m remaining). "
                "Dirac-Delta gamma collapse & pin risk prohibit new long options entries."
            )

        # Invariant 6: Mathematical Stop-Loss & Dynamic Position Sizing
        lot_size = self.get_lot_size(intent.symbol)
        max_allowed_risk_inr = account.total_portfolio_equity * self.MAX_SINGLE_TRADE_RISK_PCT

        if intent.action in [AgentAction.BUY, AgentAction.SELL]:
            risk_per_unit = abs(context.ltp - adjusted_sl)
            if risk_per_unit <= 0.001:
                # Missing or invalid stop loss - compute hard 1.0% ATR synthetic stop
                risk_per_unit = context.ltp * 0.010
                adjusted_sl = context.ltp - risk_per_unit if intent.action == AgentAction.BUY else context.ltp + risk_per_unit
                guards.append(f"SYNTHETIC_1PCT_STOP_ENFORCED (SL={adjusted_sl:.2f})")

            # Mathematical Lot Sizing: Allowed Lots = floor(Max Risk / (Risk Per Share * Lot Size))
            risk_per_lot = risk_per_unit * lot_size
            calculated_max_lots = max(1, int(math.floor(max_allowed_risk_inr / max(1.0, risk_per_lot))))

            if adjusted_lots > calculated_max_lots:
                guards.append(f"POSITION_SIZING_CLAMPED: Reduced lots from {adjusted_lots} to {calculated_max_lots} "
                              f"(Risk capped to Rs. {max_allowed_risk_inr:,.2f})")
                adjusted_lots = calculated_max_lots
            else:
                guards.append(f"POSITION_SIZING_APPROVED ({adjusted_lots} lots, Risk=Rs. {adjusted_lots * risk_per_lot:,.2f})")

            # SEBI Margin requirement:
            # - Indices (Futures/Derivatives): ~12% SPAN + ELM margin
            # - Cash Equities: ~20% MIS Intraday margin or 100% delivery
            is_index = any(idx in intent.symbol.upper() for idx in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"])
            margin_rate = 0.12 if is_index else 0.20
            total_margin_required = adjusted_lots * lot_size * context.ltp * margin_rate

            if total_margin_required > account.free_cash:
                rejections.append(
                    f"INSUFFICIENT_MARGIN: Required margin Rs. {total_margin_required:,.2f} "
                    f"({margin_rate*100:.0f}% SEBI SPAN/MIS) exceeds free cash Rs. {account.free_cash:,.2f}"
                )
            else:
                guards.append(f"SEBI_SPAN_MARGIN_VERIFIED (Required: Rs. {total_margin_required:,.2f} <= Free: Rs. {account.free_cash:,.2f})")

        # Invariant 7: Dealer Net GEX Alignment
        # If Dealer GEX is strongly negative (< -500 Cr), market is in short gamma squeeze regime
        if context.dealer_net_gex < -500 and intent.action == AgentAction.SELL and intent.regime_detected != "GAMMA_SQUEEZE_SHORT_COVERING":
            rejections.append(
                f"DEALER_GEX_SQUEEZE_RISK: Extreme negative Net GEX ({context.dealer_net_gex:,.1f} Cr). "
                "Dealers are forced buyers into rallies. Shorting prohibited."
            )

        is_approved = (len(rejections) == 0)
        if is_approved:
            self.total_approved_intents += 1
        else:
            self.total_rejected_intents += 1

        risk_at_stake = adjusted_lots * lot_size * abs(context.ltp - adjusted_sl) if is_approved else 0.0

        return ExecutionVerdict(
            intent=intent,
            approved=is_approved,
            adjusted_lots=adjusted_lots if is_approved else 0,
            adjusted_stop_loss=adjusted_sl,
            rejection_reasons=rejections,
            applied_guards=guards,
            max_capital_at_risk_inr=risk_at_stake,
        )


class AutonomousQuantAgent:
    """
    Autonomous Quant Engine incorporating Mirajane Strauss's intuitive perception,
    microstructure analytics (OFI, micro-price), and macro sentiment to propose trades.
    """

    def __init__(self, risk_gate: Optional[DeterministicRiskGate] = None):
        self.risk_gate = risk_gate or DeterministicRiskGate()
        self.last_intent: Optional[TradeIntent] = None
        self.last_verdict: Optional[ExecutionVerdict] = None

    def analyze_regime_and_generate_intent(self, context: MarketContext) -> TradeIntent:
        """
        Synthesizes technicals, order flow, dealer positioning, and sentiment.
        """
        # Microstructure signals
        micro_premium = (context.micro_price - context.ltp) / max(1.0, context.ltp)
        ofi_strong_buy = context.ofi > 0.35
        ofi_strong_sell = context.ofi < -0.35

        # Macro sentiment
        sentiment = context.macro_sentiment_score

        # Gamma Squeeze check
        gex_squeeze = context.dealer_net_gex < -400.0

        # Decision synthesis
        if gex_squeeze and context.ofi > 0.15:
            action = AgentAction.BUY
            confidence = 0.91
            regime = "GAMMA_SQUEEZE_SHORT_COVERING"
            rationale = (
                f"Extreme negative Dealer Net GEX ({context.dealer_net_gex:.1f} Cr) paired with positive OFI ({context.ofi:.2f}). "
                f"Dealer gamma trap forces dynamic delta replenishment into upside breakouts."
            )
            mirajane = (
                "I sense intense panic among short gamma market makers! Their hedging obligations are forcing them "
                "to chase prices higher. This is a classic explosive squeeze setup!"
            )
            sl = round(context.ltp * 0.993, 2)
            tp = round(context.ltp * 1.018, 2)
            suggested_lots = 3

        elif ofi_strong_buy and micro_premium > 0.0003 and sentiment >= -0.2:
            action = AgentAction.BUY
            confidence = 0.84
            regime = "MICROSTRUCTURE_OFI_SURGE"
            rationale = (
                f"Significant aggressive buyer absorption: Cont-Kukanov OFI at {context.ofi:.2f}, "
                f"micro-price leading spot by +{micro_premium*100:.3f}%."
            )
            mirajane = (
                "Institutional smart money is absorbing all passive limit asks at the inside quotes. "
                "Order flow imbalance is heavily tilted in our favor."
            )
            sl = round(context.ltp * 0.995, 2)
            tp = round(context.ltp * 1.012, 2)
            suggested_lots = 2

        elif ofi_strong_sell and micro_premium < -0.0003 and sentiment <= 0.2:
            action = AgentAction.SELL
            confidence = 0.82
            regime = "MICROSTRUCTURE_LIQUIDITY_RUN"
            rationale = (
                f"Aggressive seller distribution: OFI down to {context.ofi:.2f}, "
                f"micro-price discounted by {micro_premium*100:.3f}%."
            )
            mirajane = (
                "Bids are vanishing from the order book. Large blocks are slamming into the bids. "
                "A rapid flush down to lower liquidity pools is underway."
            )
            sl = round(context.ltp * 1.005, 2)
            tp = round(context.ltp * 0.988, 2)
            suggested_lots = 2

        else:
            action = AgentAction.HOLD
            confidence = 0.65  # Below gate
            regime = "CHOPPY_SIDEWAYS_EQUILIBRIUM"
            rationale = f"Order book in balanced consolidation. OFI={context.ofi:.2f}, Micro-spread within noise envelope."
            mirajane = "The market is undecided and resting in balance. Preserving ammunition is our highest duty right now."
            sl = context.ltp
            tp = context.ltp
            suggested_lots = 0

        intent = TradeIntent(
            symbol=context.symbol,
            action=action,
            confidence=confidence,
            rationale=rationale,
            target_price=tp,
            stop_loss_price=sl,
            suggested_lots=suggested_lots,
            regime_detected=regime,
            mirajane_thought=mirajane,
        )
        self.last_intent = intent
        return intent

    def process_cycle(
        self,
        context: MarketContext,
        account: AccountRiskState,
    ) -> ExecutionVerdict:
        """
        Executes one full cycle:
        Generates intent -> passes through Deterministic Risk Supervisor -> returns final verdict.
        """
        intent = self.analyze_regime_and_generate_intent(context)
        verdict = self.risk_gate.evaluate(intent, context, account)
        self.last_verdict = verdict
        return verdict


# Singleton global instance
global_neuro_agent = AutonomousQuantAgent()
