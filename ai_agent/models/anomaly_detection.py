"""
XAI Anomaly Detection Model (RTMD-AI equivalent)

Detects market manipulation spoofing and layering patterns using an IsolationForest.
Mandatory SEBI Compliance: Uses SHAP (SHapley Additive exPlanations) to explicitly
quantify and explain *why* an alert was triggered, satisfying "Explainable AI" laws.
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import shap

from ai_agent.models.base import BaseModel

logger = logging.getLogger(__name__)


class ManipulationDetector(BaseModel):
    """Isolation Forest anomaly detection w/ SHAP explainability."""

    def __init__(self, contamination_rate: float = 0.01) -> None:
        super().__init__(model_name="RTMD-AI_IsolationForest", version="1.0.0")
        self.contamination_rate = contamination_rate
        # In a real environment, this is trained on NSE historical spoofing patterns
        self.model = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=self.contamination_rate,
            random_state=42
        )
        self.explainer = None
        self._is_loaded = False
        self.feature_names = ['volume_spike', 'latency_ms', 'orderbook_imbalance']

    def load(self, path: str = "") -> None:
        """
        Mock loading of pretrained weights. Instead we just 'fit' a dummy set
        so the model is initialized.
        """
        # Feature 1: Volume Spike
        # Feature 2: Latency between ticks
        # Feature 3: Orderbook Ask/Bid volume imbalance ratio (Spoofing indicator)
        dummy_healthy_data = np.random.normal(loc=[100, 15, 1.0], scale=[20, 5, 0.2], size=(500, 3))
        dummy_spoof_data = np.array([
            [5000, 5, 10.0],  # Massive volume, low latency, huge imbalance
            [4500, 2, 8.5]
        ])
        
        training_data = np.vstack([dummy_healthy_data, dummy_spoof_data])
        
        self.model.fit(training_data)
        
        # Initialize SHAP explainer on the fitted Isolation Forest
        self.explainer = shap.TreeExplainer(self.model)
        self._is_loaded = True
        logger.info(f"{self.model_name} loaded and fitted with XAI SHAP capabilities.")

    def save(self, path: str) -> None:
        pass

    def predict(self, features: pd.DataFrame | np.ndarray) -> Dict[str, Any]:
        """
        Runs anomaly detection and triggers SHAP TreeExplainer if an anomaly
        is detected, outputting the human-readable reasoning.
        """
        if not self._is_loaded:
            self.load()

        if isinstance(features, pd.DataFrame):
            X = features.values
        else:
            X = np.asarray(features)

        # Sklearn returns 1 for inliers, -1 for outliers/anomalies
        predictions = self.model.predict(X)
        anomaly_scores = self.model.score_samples(X) # Negative distances

        results = []
        for i, pred in enumerate(predictions):
            is_anomaly = (pred == -1)
            
            # Inverse score so anomaly is bounded ~0.0 to 1.0
            confidence = abs(anomaly_scores[i]) 
            confidence = min(confidence, 1.0)
            
            signal_data = {
                "signal": "MANIPULATION_DETECTED" if is_anomaly else "NORMAL",
                "confidence": float(confidence),
                "metadata": {}
            }

            # If SEBI requires it, we run SHAP to explain exactly why this tick was flagged
            if is_anomaly:
                shap_values = self.explainer.shap_values(X[i].reshape(1, -1))
                # shap_values is an array corresponding to features
                contribs = {}
                for j, feat_name in enumerate(self.feature_names):
                    # How much this feature pushed the model toward predicting -1
                    contribs[feat_name] = float(shap_values[j] if len(shap_values.shape) == 1 else shap_values[0][j])
                
                # Identify the dominant feature
                dominant_feature = max(contribs, key=lambda k: abs(contribs[k]))
                
                signal_data["metadata"] = {
                    "shap_contributions": contribs,
                    "explanation": f"Flagged primarily due to anomalous {dominant_feature}."
                }
                
                logger.warning(f"[RTMD-AI ALERT] {signal_data['metadata']['explanation']}")
            
            results.append(signal_data)
            
        return results[0] if len(results) == 1 else results
