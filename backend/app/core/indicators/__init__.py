"""
Proprietary Indian Technical Analysis Library.
All indicators implemented from mathematical first principles.
Optimized for NSE/BSE market microstructure.
"""
from .indian_ta_library import IndianTALibrary, SignalResult
from .multi_timeframe_engine import MultiTimeframeEngine, MultiTimeframeSignal

__all__ = ["IndianTALibrary", "SignalResult", "MultiTimeframeEngine", "MultiTimeframeSignal"]
