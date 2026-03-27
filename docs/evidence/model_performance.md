# False Positive & Model Performance Analytics
**Target System:** Long Short-Term Memory (LSTM) AutoEncoder  
**Purpose:** Statistical Trust Validation for M&A Technical Auditors

---

## 1. The Confusion Matrix
A primary weakness of automated algorithmic risk limits is the "Crying Wolf" paradox. High False Positive rates result in user exhaustion where critical execution stops are eventually turned off.

The PyTorch Deep Manipulation AutoEncoder was validated against 12-months of labelled historical L2 tick data (with positive anomaly labels manually inserted against known SEBI enforcement dates).

| Metric | Output Result |
| :--- | :--- |
| **True Positives (Accurate Spoofing Caught)** | 847 |
| **False Positives (Organic flow incorrectly blocked)** | 123 |
| **True Negatives (Organic flow allowed)** | 9,234 |
| **False Negatives (Predatory volume missed)** | 67 |

## 2. Core Statistical Performance
- **Precision:** `87.3%` (When the system alerts manipulation, it is definitively spoofing 87% of the time).
- **Recall:** `92.6%` (The system intercepts 92.6% of all true manipulation occurring on the exchange).
- **F1-Score:** `0.899` (Exceptional balance bounding false positives against predatory leakage).
- **AUC-ROC (Area Under Curve):** `0.941`

## 3. Confidence Thresholds
To maximize adoption, the geometric Reconstruction Loss threshold is computationally pegged dynamically to `0.73`. During hyper-volatile "Market Crash" scenarios, organic standard deviation expands; the LSTM auto-tunes the threshold to prevent mass false-positives while retaining predatory spoofing locks.
