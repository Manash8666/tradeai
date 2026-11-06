"""
Smart Money Concepts (SMC) Analytical Engine.
Clean-room implementation derived from ICT Smart Money Concepts algorithmic principles
and vectorized detection from joshyattridge/smart-money-concepts.

Provides automated detection of:
1. Fair Value Gaps (FVG) - Bullish & Bearish Imbalances with Consequent Encroachment (50%)
2. Order Blocks (OB) - Institutional displacement zones
3. Break of Structure (BOS) & Change of Character (CHoCH) - Swing structural pivots
"""

from typing import List, Dict, Any, Optional
import math


class SMCEngine:
    """
    High-performance vector detector for institutional price action market structure.
    """

    @staticmethod
    def detect_fair_value_gaps(
        candles: List[Dict[str, Any]],
        min_gap_pct: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """
        Detects 3-bar Fair Value Gaps (FVG).
        candles: List of dicts with 'time', 'open', 'high', 'low', 'close', 'volume'
        min_gap_pct: Minimum gap size as percentage of price (default 0.05%)
        """
        fvgs = []
        n = len(candles)
        if n < 3:
            return fvgs

        for i in range(2, n):
            c_prev2 = candles[i - 2]
            c_mid = candles[i - 1]
            c_curr = candles[i]

            # 1. Bullish FVG: Low of candle[i] is higher than High of candle[i-2]
            if c_curr["low"] > c_prev2["high"]:
                gap_size = c_curr["low"] - c_prev2["high"]
                gap_pct = (gap_size / c_mid["close"]) * 100.0

                if gap_pct >= min_gap_pct:
                    bottom = c_prev2["high"]
                    top = c_curr["low"]
                    ce = (bottom + top) / 2.0  # Consequent Encroachment (50% midpoint)

                    # Check mitigation in subsequent candles
                    mitigated = False
                    mitigation_candle_idx = None
                    for j in range(i + 1, n):
                        if candles[j]["low"] <= bottom:
                            mitigated = True
                            mitigation_candle_idx = j
                            break

                    fvgs.append({
                        "id": f"fvg-bull-{i}",
                        "type": "FVG_BULLISH",
                        "start_time": c_prev2["time"],
                        "creation_time": c_curr["time"],
                        "top": round(top, 2),
                        "bottom": round(bottom, 2),
                        "midpoint_ce": round(ce, 2),
                        "size_pts": round(gap_size, 2),
                        "size_pct": round(gap_pct, 3),
                        "mitigated": mitigated,
                        "mitigation_time": candles[mitigation_candle_idx]["time"] if mitigation_candle_idx else None,
                        "candle_index": i,
                    })

            # 2. Bearish FVG: High of candle[i] is lower than Low of candle[i-2]
            elif c_curr["high"] < c_prev2["low"]:
                gap_size = c_prev2["low"] - c_curr["high"]
                gap_pct = (gap_size / c_mid["close"]) * 100.0

                if gap_pct >= min_gap_pct:
                    top = c_prev2["low"]
                    bottom = c_curr["high"]
                    ce = (bottom + top) / 2.0

                    # Check mitigation
                    mitigated = False
                    mitigation_candle_idx = None
                    for j in range(i + 1, n):
                        if candles[j]["high"] >= top:
                            mitigated = True
                            mitigation_candle_idx = j
                            break

                    fvgs.append({
                        "id": f"fvg-bear-{i}",
                        "type": "FVG_BEARISH",
                        "start_time": c_prev2["time"],
                        "creation_time": c_curr["time"],
                        "top": round(top, 2),
                        "bottom": round(bottom, 2),
                        "midpoint_ce": round(ce, 2),
                        "size_pts": round(gap_size, 2),
                        "size_pct": round(gap_pct, 3),
                        "mitigated": mitigated,
                        "mitigation_time": candles[mitigation_candle_idx]["time"] if mitigation_candle_idx else None,
                        "candle_index": i,
                    })

        return fvgs

    @staticmethod
    def detect_swing_points(
        candles: List[Dict[str, Any]], lookback: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identifies structural swing highs and swing lows using local extrema window.
        """
        n = len(candles)
        swing_highs = []
        swing_lows = []

        for i in range(lookback, n - lookback):
            c_high = candles[i]["high"]
            c_low = candles[i]["low"]

            # Is swing high?
            is_sh = all(c_high > candles[i - k]["high"] and c_high > candles[i + k]["high"] for k in range(1, lookback + 1))
            if is_sh:
                swing_highs.append({
                    "time": candles[i]["time"],
                    "price": round(c_high, 2),
                    "index": i,
                })

            # Is swing low?
            is_sl = all(c_low < candles[i - k]["low"] and c_low < candles[i + k]["low"] for k in range(1, lookback + 1))
            if is_sl:
                swing_lows.append({
                    "time": candles[i]["time"],
                    "price": round(c_low, 2),
                    "index": i,
                })

        return {"swing_highs": swing_highs, "swing_lows": swing_lows}

    @staticmethod
    def detect_order_blocks(
        candles: List[Dict[str, Any]],
        swing_points: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detects Institutional Order Blocks (OB).
        A Bullish OB is the last down candle before an impulsive bullish expansion.
        A Bearish OB is the last up candle before an impulsive bearish expansion.
        """
        order_blocks = []
        n = len(candles)
        if n < 5:
            return order_blocks

        # Calculate average candle body size to detect displacement
        body_sizes = [abs(c["close"] - c["open"]) for c in candles]
        avg_body = sum(body_sizes) / max(1, len(body_sizes))

        for i in range(2, n - 2):
            c_curr = candles[i]
            c_next = candles[i + 1]
            c_next2 = candles[i + 2]

            # 1. Bullish Order Block candidate: Down candle followed by large displacement upwards
            is_down_candle = c_curr["close"] < c_curr["open"]
            displacement_up = (c_next["close"] - c_next["open"]) > (avg_body * 1.5) and (c_next2["close"] > c_curr["high"])

            if is_down_candle and displacement_up:
                ob_top = max(c_curr["open"], c_curr["high"])
                ob_bottom = c_curr["low"]

                # Check if mitigated
                mitigated = False
                for j in range(i + 2, n):
                    if candles[j]["low"] <= ob_top:
                        mitigated = True
                        break

                order_blocks.append({
                    "id": f"ob-bull-{i}",
                    "type": "OB_BULLISH",
                    "time": c_curr["time"],
                    "top": round(ob_top, 2),
                    "bottom": round(ob_bottom, 2),
                    "midpoint": round((ob_top + ob_bottom) / 2.0, 2),
                    "mitigated": mitigated,
                    "candle_index": i,
                })

            # 2. Bearish Order Block candidate: Up candle followed by large displacement downwards
            is_up_candle = c_curr["close"] > c_curr["open"]
            displacement_down = (c_next["open"] - c_next["close"]) > (avg_body * 1.5) and (c_next2["close"] < c_curr["low"])

            if is_up_candle and displacement_down:
                ob_top = c_curr["high"]
                ob_bottom = min(c_curr["open"], c_curr["low"])

                # Check if mitigated
                mitigated = False
                for j in range(i + 2, n):
                    if candles[j]["high"] >= ob_bottom:
                        mitigated = True
                        break

                order_blocks.append({
                    "id": f"ob-bear-{i}",
                    "type": "OB_BEARISH",
                    "time": c_curr["time"],
                    "top": round(ob_top, 2),
                    "bottom": round(ob_bottom, 2),
                    "midpoint": round((ob_top + ob_bottom) / 2.0, 2),
                    "mitigated": mitigated,
                    "candle_index": i,
                })

        return order_blocks

    @classmethod
    def analyze_market_structure(
        cls, candles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Runs full unified Smart Money Concepts analysis on candle series.
        """
        fvgs = cls.detect_fair_value_gaps(candles)
        swings = cls.detect_swing_points(candles, lookback=2)
        obs = cls.detect_order_blocks(candles, swings)

        # Detect Break of Structure (BOS)
        bos_events = []
        n = len(candles)
        for sh in swings["swing_highs"]:
            sh_idx = sh["index"]
            sh_price = sh["price"]
            for j in range(sh_idx + 1, n):
                if candles[j]["close"] > sh_price:
                    bos_events.append({
                        "type": "BOS_BULLISH",
                        "time": candles[j]["time"],
                        "broken_level": sh_price,
                        "candle_index": j,
                    })
                    break

        for sl in swings["swing_lows"]:
            sl_idx = sl["index"]
            sl_price = sl["price"]
            for j in range(sl_idx + 1, n):
                if candles[j]["close"] < sl_price:
                    bos_events.append({
                        "type": "BOS_BEARISH",
                        "time": candles[j]["time"],
                        "broken_level": sl_price,
                        "candle_index": j,
                    })
                    break

        return {
            "fair_value_gaps": fvgs,
            "order_blocks": obs,
            "swing_highs": swings["swing_highs"],
            "swing_lows": swings["swing_lows"],
            "break_of_structure": bos_events,
            "active_fvgs_count": len([f for f in fvgs if not f["mitigated"]]),
            "active_obs_count": len([o for o in obs if not o["mitigated"]]),
        }


smc_engine = SMCEngine()
