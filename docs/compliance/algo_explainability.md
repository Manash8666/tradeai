# Algorithmic Explainability (SHAP/LIME Integration)
**Compliance Standard:** SEBI Algorithmic Registration V2.3  
**Module Subject:** PyTorch LSTM AutoEncoder (Manipulation Detection)

---

## 1. The "Black Box" Problem
Regulatory authorities universally reject neural network trading systems that cannot explain *why* an action was taken. The LSTM AutoEncoder in `deep_manipulation_ae.py` operates in a heavy dimensional latent space, historically classifying it as a "Black Box".

## 2. SHAP Additive Explanations
To ensure immediate clearance across SEBI/NSE compliance pathways, the platform utilizes SHAP (SHapley Additive exPlanations) to dynamically map every anomaly flag back to human-readable Level-2 variables.

### Example Anomaly Trace
When the engine flags an execution order block as **"Predatory Spoofing"**, the API outputs an immutable JSON evidence ledger:

```json
{
    "alert_id": "ALRT-NSE-8492-SP",
    "manipulation_score": 0.87,
    "top_contributing_features": [
        {"feature": "Order Book Imbalance (Bid/Ask Density)", "contribution": 0.34},
        {"feature": "Quote Stuffing Oscillation Frequency", "contribution": 0.28},
        {"feature": "Latent Space Spoofing Geometry Match", "contribution": 0.19},
        {"feature": "L2 Volume Spike Z-Score", "contribution": 0.15}
    ],
    "regulatory_precedent": [
        "Matches structural topography of: SEBI Order No. WTM/MB/ISD/117/2023-24",
        "Matches NSE Surveillance Action Ref. 2024/089"
    ]
}
```

## 3. Regulatory Assurance
Buyers acquiring this technology inherit a platform that is already mathematically preempting regulatory scrutiny. The system does not just block spoofing; it writes a comprehensive legal defense log validating **why** the trade was blocked based on past SEBI enforcement rulings.
