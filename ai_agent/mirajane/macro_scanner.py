import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any
import zoneinfo

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


@dataclass
class MacroMatrix:
    brent_crude_usd: float
    us_10y_yield_pct: float
    dxy_index: float
    gift_nifty_spread: float  # Points above/below NSE closing level
    sp500_futures_pct: float
    nikkei_225_pct: float
    crude_impact_on_india: str
    dxy_impact_on_inr: str
    global_thrust_vector: float  # -1.0 to +1.0
    sentiment_tag: str
    ist_timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GlobalMacroScanner:
    """
    Global Macro Transmission Scanner.
    Synthesizes international macro factors (Brent Crude, US 10Y Yields, Dollar Index, Asian Overnight)
    and quantifies their deterministic transmission onto the Dalal Street opening structure.
    """

    def __init__(self):
        # Baseline benchmarks for Indian economy
        self.crude_benign_threshold = 80.0   # Crude < $80 is strongly bullish for Indian current account
        self.crude_critical_threshold = 88.0 # Crude > $88 induces inflation drag
        self.us_yield_high_threshold = 4.35  # > 4.35% triggers emerging market capital flight
        self.dxy_critical_threshold = 104.5  # > 104.5 pressures USD/INR towards 84+

    def scan_global_macro(self, overrides: Dict[str, Any] | None = None) -> MacroMatrix:
        """
        Gathers current global macro parameters, calculates cross-asset impact vectors,
        and outputs a unified MacroMatrix for Mirajane's cognitive engine.
        """
        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        overrides = overrides or {}

        # Default live market approximations (overridable via API inputs or live feeds)
        brent_crude = float(overrides.get("brent_crude_usd", 81.20))
        us_10y = float(overrides.get("us_10y_yield_pct", 4.19))
        dxy = float(overrides.get("dxy_index", 103.85))
        gift_spread = float(overrides.get("gift_nifty_spread", 28.5))
        sp500_futures = float(overrides.get("sp500_futures_pct", 0.42))
        nikkei = float(overrides.get("nikkei_225_pct", 0.65))

        # 1. Crude Oil Impact on India (Major oil importer)
        if brent_crude < self.crude_benign_threshold:
            crude_impact = "FAVORABLE (Fiscal Tailwind)"
            crude_score = 0.40
        elif brent_crude > self.crude_critical_threshold:
            crude_impact = "SEVERE_DRAG (Current Account Deficit Pressure)"
            crude_score = -0.60
        else:
            crude_impact = "MODERATE (Within Fiscal Comfort Band)"
            crude_score = 0.05

        # 2. DXY & US Yield Impact on Indian Rupee & FII Flows
        if dxy > self.dxy_critical_threshold or us_10y > self.us_yield_high_threshold:
            dxy_impact = "DEPRECIATION_PRESSURE (FII Outflow Risk)"
            fx_score = -0.45
        elif dxy < 102.5:
            dxy_impact = "STRONG_INR (Aggressive FII Inflow Magnet)"
            fx_score = 0.50
        else:
            dxy_impact = "STABLE (Range-bound INR)"
            fx_score = 0.10

        # 3. Overnight Asian / US Handover Momentum
        overnight_score = (gift_spread / 50.0) * 0.40 + (sp500_futures / 1.0) * 0.35 + (nikkei / 1.0) * 0.25
        overnight_score = max(-0.80, min(0.80, overnight_score))

        # 4. Composite Global Thrust Vector (-1.0 to +1.0)
        global_thrust = round(
            max(-1.0, min(1.0, (overnight_score * 0.45) + (crude_score * 0.30) + (fx_score * 0.25))),
            2,
        )

        if global_thrust >= 0.35:
            sentiment_tag = "RISK_ON (Global Tailwinds Active)"
        elif global_thrust <= -0.35:
            sentiment_tag = "RISK_OFF (Global Headwinds Dominant)"
        else:
            sentiment_tag = "NEUTRAL_BALANCED"

        matrix = MacroMatrix(
            brent_crude_usd=brent_crude,
            us_10y_yield_pct=us_10y,
            dxy_index=dxy,
            gift_nifty_spread=gift_spread,
            sp500_futures_pct=sp500_futures,
            nikkei_225_pct=nikkei,
            crude_impact_on_india=crude_impact,
            dxy_impact_on_inr=dxy_impact,
            global_thrust_vector=global_thrust,
            sentiment_tag=sentiment_tag,
            ist_timestamp=now_str,
        )

        logger.info(f"[MIRAJANE MACRO] Global Thrust: {global_thrust:+.2f} ({sentiment_tag})")
        return matrix


global_macro_scanner = GlobalMacroScanner()
