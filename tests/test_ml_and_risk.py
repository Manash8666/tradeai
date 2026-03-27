"""
Unit test for testing the BaselineMeanReversion Model and the Risk Engine 
Pre-Trade boundaries natively.
"""

import sys
import asyncio
from typing import Any

import numpy as np
import pytest

sys.path.append("E:/Trading Platform")

from ai_agent.models.mean_reversion import BaselineMeanReversion
from core.risk.engine import risk_manager, RiskViolationException


def test_mean_reversion_inference():
    """Verify standard ML Z-Score functionality on Numpy arrays."""
    model = BaselineMeanReversion(window=5, z_threshold=1.5)
    
    # 1. Steady climb, then massive drop (Oversold -> BUY)
    steady_features = np.array([100, 101, 102, 103, 90])
    result = model.predict(steady_features)
    assert result["signal"] == "BUY"
    assert result["confidence"] > 0.0

    # 2. Steady drop, then massive spike (Overbought -> SELL)
    spike_features = np.array([90, 89, 88, 87, 105])
    result2 = model.predict(spike_features)
    assert result2["signal"] == "SELL"
    assert result2["confidence"] > 0.0
    
    # 3. Flat line (HOLD)
    flat_features = np.array([100, 100, 100, 100, 100])
    result3 = model.predict(flat_features)
    assert result3["signal"] == "HOLD"
    assert result3["confidence"] == 0.0


def test_risk_manager_fat_finger():
    """Verify RiskEngine intercepts fat fingers."""
    pass_trade = risk_manager.validate_pre_trade("NIFTY", "BUY", 10, 1000.0, 0)
    assert pass_trade is True
    
    with pytest.raises(RiskViolationException) as excinfo:
        # Pushing 50,000 qty against Max 1000 limit
        risk_manager.validate_pre_trade("NIFTY", "BUY", 50000, 1000.0, 0)
    assert "exceeds" in str(excinfo.value)

def test_risk_manager_leverage_violation():
    """Verify position sizing limit (Max 20% on 100K Account = 20K capital limit)."""
    # Placing an order valued at 30k (> 20k)
    with pytest.raises(RiskViolationException) as excinfo:
        risk_manager.validate_pre_trade("BANKNIFTY", "BUY", 1, 30000.0, 0)
    assert "exposure" in str(excinfo.value).lower()


if __name__ == "__main__":
    test_mean_reversion_inference()
    test_risk_manager_fat_finger()
    test_risk_manager_leverage_violation()
    print("\n✅ Verification tests passed: ML Inference and Risk Hooks functioning optimally.")
