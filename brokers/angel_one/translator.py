"""
Angel One Order Request Translator

Translates between NautilusTrader execution payloads and the SmartAPI
dictionary structures required by Angel One. Ensures regulatory parameters
like product types (INTRADAY vs DELIVERY) and order tags (Algo ID) are
passed correctly.
"""

from typing import Any, Dict


class AngelOneTranslator:
    """Translation layer for Angel One specific protocol."""

    EXCHANGE_MAP = {
        "NSE": "NSE",
        "BSE": "BSE",
        "NFO": "NFO",
        "MCX": "MCX"
    }

    PRODUCT_TYPE_MAP = {
        "INTRADAY": "INTRADAY",
        "DELIVERY": "DELIVERY",
        "CARRYFORWARD": "CARRYFORWARD"
    }

    ORDER_TYPE_MAP = {
        "MARKET": "MARKET",
        "LIMIT": "LIMIT",
        "STOPLOSS_LIMIT": "STOPLOSS_LIMIT",
        "STOPLOSS_MARKET": "STOPLOSS_MARKET"
    }

    @classmethod
    def to_broker_order(
        cls,
        symbol: str,
        qty: int,
        side: str,
        order_type: str,
        exchange: str = "NSE",
        product_type: str = "INTRADAY",
        price: float = 0.0,
        algo_id: str | None = None,
    ) -> Dict[str, Any]:
        """Convert standard parameters into Angel One SmartAPI request dict."""
        
        # Validations
        if exchange not in cls.EXCHANGE_MAP.values():
            raise ValueError(f"Exchange {exchange} not supported by Angel One Translator")

        if product_type not in cls.PRODUCT_TYPE_MAP.values():
            raise ValueError(f"Product type {product_type} not supported by Angel One Translator")
            
        request = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": "placeholder_from_instrument_def",  # Requires mapping service
            "transactiontype": "BUY" if side.upper() == "BUY" else "SELL",
            "exchange": exchange,
            "ordertype": cls.ORDER_TYPE_MAP.get(order_type.upper(), "MARKET"),
            "producttype": product_type,
            "duration": "DAY",
            "price": str(price) if price > 0 else "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": str(qty)
        }

        # SEBI Compliance: Tag Algo ID into order if provided
        if algo_id:
            request["ordertag"] = algo_id

        return request
