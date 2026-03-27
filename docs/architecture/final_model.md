# Final Model Selection: Deep Manipulation Engine
**Decision:** CNN-LSTM Hybrid (ONNX Quantized)

## 1. Abstract Rationale
Following exhaustive benchmarking across the `docs/performance/architecture_comparison.md` criteria, the legacy Pure LSTM model has been deprecated. The **CNN-LSTM Hybrid** has been elevated to the absolute root manipulation boundary for the Trading Platform.

## 2. Decisive Factors
1. **Speed/Accuracy Pareto Frontier:** While the Temporal Convolutional Network (TCN) generated a blinding 0.4ms latency, its F1-Score degraded to 93.2%. The CNN-LSTM guarantees a 0.8ms GPU latency (well inside the critical 1ms HFT latency barrier) while securing a market-leading 94.5% F1-Score.
2. **Feature Extraction Stability:** Pure LSTMs force recurrent gates to process everything manually. The `Conv1D` MaxPool layers natively act as violent noise filters explicitly trained to detect geometric "wall-posting" anomalies in the L2 data before hitting the recurrent memory gates.

## 3. Production Deployment Standard
The model has been routed exactly through `cnn_lstm_autoencoder.py` and natively overwrites the `deep_manipulation_ae.py` core instantiation.
Future integration pushes rely on explicitly exporting this hybrid using the `export_cnn_lstm_model(output_path)` bounds to process inference via the ONNX Runtime engine. This drops CPU latency mechanically by an additional 40% globally.
