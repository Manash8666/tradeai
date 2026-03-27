"""
Inference Engine

Routes real-time tick/bar data slices from NautilusTrader into the loaded 
AI Models and returns actionable predictive signals.
"""

import logging
from typing import Any, Dict

import numpy as np

from ai_agent.models.base import BaseModel
from ai_agent.models.mean_reversion import BaselineMeanReversion
from ai_agent.models.anomaly_detection import ManipulationDetector

logger = logging.getLogger(__name__)


class InferenceEngine:
    """Manages ML model lifecycle and real-time inference execution."""

    def __init__(self) -> None:
        self.models: Dict[str, BaseModel] = {}
        logger.info("InferenceEngine initialized.")

    def load_model(
        self, model_id: str, model_type: str = "mean_reversion", path: str | None = None
    ) -> None:
        """Load a model into memory."""
        if model_type == "mean_reversion":
            model = BaselineMeanReversion(window=20, z_threshold=2.0)
            # path is ignored for statistical models currently
        elif model_type == "rtmd_ai":
            model = ManipulationDetector()
            model.load()
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        self.models[model_id] = model
        logger.info(f"Loaded model {model_id} ({model.model_name} v{model.version})")

    def run_inference(self, model_id: str, features: list[float] | np.ndarray) -> Dict[str, Any]:
        """Execute the prediction for a given feature set."""
        if model_id not in self.models:
            raise KeyError(f"Model ID {model_id} not loaded in InferenceEngine.")

        model = self.models[model_id]
        array_features = np.asarray(features)

        # Execute prediction
        result = model.predict(array_features)

        logger.debug(
            f"Inference [{model_id}]: {result['signal']} @ {result['confidence']:.2f} conf"
        )
        return result


# Global singleton for FastAPI and Strategy execution
inference_engine = InferenceEngine()
