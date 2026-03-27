"""
Message Bus for Event-Driven Architecture

Bridges NautilusTrader internal events to our external UI via FastAPI WebSockets
and tracks critical audit trails for SEBI compliance.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

class MessageBus:
    """Async Pub/Sub message bus for bridging Core Engine events to WebSockets."""
    
    def __init__(self) -> None:
        # topic -> list of async callback functions
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}
    
    def subscribe(self, topic: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Subscribe to a specific topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
        logger.debug(f"Subscribed to topic: {topic}")
        
    def unsubscribe(self, topic: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Remove a subscription from a topic."""
        if topic in self._subscribers and callback in self._subscribers[topic]:
            self._subscribers[topic].remove(callback)

    async def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        """Publish a message payload to all subscribers of the given topic asynchronously."""
        if topic not in self._subscribers:
            return
            
        tasks = [
            asyncio.create_task(self._safe_invoke(callback, payload))
            for callback in self._subscribers[topic]
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_invoke(self, callback: Callable[[Dict[str, Any]], Any], payload: Dict[str, Any]) -> None:
        """Safely invoke an async callback catching any exceptions to prevent bus crashes."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(payload)
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, callback, payload)
        except Exception as e:
            logger.error(f"Error in message bus callback: {e}", exc_info=True)


# Global singleton instance
message_bus = MessageBus()
