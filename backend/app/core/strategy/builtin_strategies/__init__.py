"""
Proprietary Built-in Strategies for Indian Markets (NSE/BSE).
Zero third-party code. Re-engineered from mathematical first principles.
"""
from .momentum_reversal import BankNiftyMomentumReversal
from .gap_fade import GIFTNiftyGapFade
from .vix_spike_hedge import IndiaVIXSpikeHedge
from .expiry_gamma_squeeze import ExpiryGammaSqueeze
from .fii_flow_follower import FIIFlowFollower

STRATEGY_REGISTRY = {
    "BANKNIFTY_MOMENTUM": BankNiftyMomentumReversal,
    "GIFT_GAP_FADE": GIFTNiftyGapFade,
    "VIX_HEDGE": IndiaVIXSpikeHedge,
    "GAMMA_SQUEEZE": ExpiryGammaSqueeze,
    "FII_FOLLOWER": FIIFlowFollower,
}

__all__ = [
    "BankNiftyMomentumReversal",
    "GIFTNiftyGapFade",
    "IndiaVIXSpikeHedge",
    "ExpiryGammaSqueeze",
    "FIIFlowFollower",
    "STRATEGY_REGISTRY",
]
