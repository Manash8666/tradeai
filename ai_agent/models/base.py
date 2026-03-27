"""
Standardized ML Inference Interface

All statistical, machine learning, and deep learning models must inherit
from this base class to ensure clean integration with the Inference Engine.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

import numpy as np
import pandas as pd


class BaseModel(ABC):
    """Abstract Base Class for trading AI models."""

    def __init__(self, model_name: str, version: str) -> None:
        self.model_name = model_name
        self.version = version
        self._is_loaded = False

    @abstractmethod
    def load(self, path: str) -> None:
        """Load pretrained model weights from disk."""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Save trained model weights to disk."""
        pass

    @abstractmethod
    def predict(self, features: pd.DataFrame | np.ndarray) -> Dict[str, Any]:
        """
        Run inference on the provided feature set.
        
        Returns:
            Dict containing standardized prediction keys:
            - 'signal': str (BUY/SELL/HOLD)
            - 'confidence': float (0.0 to 1.0)
            - 'predicted_price': Optional[float]
            - 'metadata': dict
        """
        pass

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
