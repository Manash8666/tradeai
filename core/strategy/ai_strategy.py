"""
AI Intelligence Strategy

Links the high-performance execution of NautilusTrader with the `InferenceEngine`.
Triggers the ML models on every Nth tick or bar completion.
"""

from nautilus_trader.model.data.quote import QuoteTick

from ai_agent.inference_engine import inference_engine
from core.message_bus import message_bus
from core.strategy.base import BaseStrategy


class AITradingStrategy(BaseStrategy):
    """Executes trades based on AI Inference signals."""

    def __init__(self, config) -> None:
        super().__init__(config)
        self.model_id = config.get("model_id", "baseline_v1")
        self.symbol = config.get("symbol", "NIFTY50")
        self.active_position = False
        self.tick_buffer = []

    def on_start(self) -> None:
        super().on_start()
        # Ensure the model is loaded in the Inference Engine
        try:
            inference_engine.load_model(self.model_id)
        except Exception as e:
            self.log.error(f"Failed to load AI model {self.model_id}: {e}")
            self.stop()

    async def _publish_signal(self, signal: str, confidence: float, price: float):
        """Broadcast signal over Message Bus for frontend."""
        await message_bus.publish(
            "ai_signals",
            {
                "symbol": self.symbol,
                "signal": signal,
                "confidence": confidence,
                "timestamp": self.node.clock.timestamp_ms(),
                "price": price,
            },
        )

    def on_quote_tick(self, tick: QuoteTick) -> None:
        """Process real-time ticks and request inference."""
        if str(tick.instrument_id.symbol) != self.symbol:
            return

        price = tick.ask_price.as_double()
        self.tick_buffer.append(price)

        # Basic batching: Run inference every time we get enough data
        if len(self.tick_buffer) >= 20:
            # Slice the last 20 for inference
            features = self.tick_buffer[-20:]

            # Predict
            prediction = inference_engine.run_inference(self.model_id, features)
            signal = prediction["signal"]
            confidence = prediction["confidence"]

            # Non-blocking async publish to UI
            # (Note: In strict Nautilus production, passing async to the bus
            # from synchronous on_quote_tick requires a thread-safe queue jump)
            import asyncio

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._publish_signal(signal, confidence, price))
            except RuntimeError:
                pass  # Event loop not running in backtest mode

            # Naive Execution Logic
            if signal == "BUY" and not self.active_position:
                self.log.info(f"AI Signal: BUY at {price} (Conf: {confidence})")
                self.active_position = True

            elif signal == "SELL" and self.active_position:
                self.log.info(f"AI Signal: SELL at {price} (Conf: {confidence})")
                self.active_position = False

            # Slide window
            self.tick_buffer.pop(0)
