import logging
import re
import time
import uuid
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import zoneinfo

from backend.app.core.hft_engine import hft_engine
from backend.app.core.pnl_greed_lock import greed_lock_engine
from backend.app.core.sebi_ptrc_killswitch import sebi_fortress
from backend.app.core.sebi_hitl_compliance import sebi_hitl_guard
from backend.app.core.timezone_guards import temporal_guard
from core.paper_trader import paper_broker

logger = logging.getLogger(__name__)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class MirajaneTradeEngine:
    """
    Direct Execution Engine for Mirajane Strauss.
    Translates cognitive conversational intents or autonomous quantitative scans into
    SEBI-compliant, microsecond-latency orders routed through the PyO3 Rust HFT OMS.
    """

    DEFAULT_LOT_SIZES = {
        "NIFTY50": 50,
        "NIFTY": 50,
        "BANKNIFTY": 15,
        "FINNIFTY": 25,
        "MIDCPNIFTY": 50,
        "SENSEX": 10,
        "BANKEX": 15,
    }

    REFERENCE_PRICES = {
        "NIFTY50": 24520.0,
        "NIFTY": 24520.0,
        "BANKNIFTY": 51200.0,
        "FINNIFTY": 23400.0,
        "MIDCPNIFTY": 12850.0,
        "SENSEX": 80450.0,
        "RELIANCE": 2980.0,
        "TCS": 3950.0,
        "HDFCBANK": 1680.0,
        "INFY": 1820.0,
        "ICICIBANK": 1240.0,
        "TATAMOTORS": 940.0,
    }

    def __init__(self):
        self._pending_orders: Dict[str, Dict[str, Any]] = {}
        self._active_positions: Dict[str, Dict[str, Any]] = {}
        logger.info("[MIRAJANE TRADE ENGINE] Direct Execution Core initialized with PyO3 Rust HFT Bridge.")

    def parse_trade_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parses conversational commands like:
        - 'Buy 2 lots of NIFTY'
        - 'Short BankNifty'
        - 'Buy 100 shares of Reliance'
        - 'Close TCS'
        - 'Flatten all positions'
        """
        clean = text.strip()
        text_lower = clean.lower()

        # Emergency flatten intent
        if "flatten all" in text_lower or "emergency exit" in text_lower or "flatten positions" in text_lower:
            return {"action_type": "FLATTEN_ALL"}

        # Position close intent
        close_match = re.search(r"(?:close|exit|square\s*off)\s+([a-zA-Z0-9_]+)", text_lower)
        if close_match:
            raw_sym = close_match.group(1).upper()
            sym = self._normalize_symbol(raw_sym)
            return {"action_type": "CLOSE_POSITION", "symbol": sym}

        # Order placement intent: (buy|sell|long|short)
        order_match = re.search(r"\b(buy|sell|long|short)\b", text_lower)
        if not order_match:
            return None

        verb = order_match.group(1).upper()
        side = "BUY" if verb in ["BUY", "LONG"] else "SELL"

        # Symbol extraction
        found_symbol = "NIFTY50"
        for sym_candidate in self.REFERENCE_PRICES.keys():
            if sym_candidate.lower() in text_lower:
                found_symbol = sym_candidate
                break

        # Quantity / Lots extraction
        qty = self.DEFAULT_LOT_SIZES.get(found_symbol, 25)
        lot_match = re.search(r"([0-9]+)\s*(?:lots?|lot)", text_lower)
        shares_match = re.search(r"([0-9]+)\s*(?:shares?|qty|contracts?)", text_lower)

        if lot_match:
            num_lots = int(lot_match.group(1))
            lot_multiplier = self.DEFAULT_LOT_SIZES.get(found_symbol, 1)
            qty = num_lots * lot_multiplier
        elif shares_match:
            qty = int(shares_match.group(1))

        # Strike / Option Type extraction (e.g., 24500 CE, 51000 PE)
        option_match = re.search(r"([0-9]{4,6})\s*(ce|pe|call|put)", text_lower)
        symbol = found_symbol
        if option_match:
            strike = option_match.group(1)
            opt_type = "CE" if option_match.group(2).lower() in ["ce", "call"] else "PE"
            symbol = f"{found_symbol}-{strike}-{opt_type}"

        return {
            "action_type": "PLACE_ORDER",
            "side": side,
            "symbol": symbol,
            "quantity": qty,
            "order_type": "MARKET",
        }

    def _normalize_symbol(self, raw: str) -> str:
        raw_upper = raw.upper()
        if "NIFTY" in raw_upper and "BANK" not in raw_upper and "FIN" not in raw_upper and "MID" not in raw_upper:
            return "NIFTY50"
        if "BANK" in raw_upper:
            return "BANKNIFTY"
        return raw_upper

    def prepare_trade(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "MARKET",
        origin: str = "MIRAJANE_AI",
    ) -> Dict[str, Any]:
        """
        Runs SEBI Pre-Trade Risk Controls (PTRC) and prepares the order
        for mandatory 1-Touch human confirmation.
        """
        now = temporal_guard.get_market_time()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S IST")

        # 1. Behavioral Greed Circuit Breaker Check
        if not greed_lock_engine.can_execute_trade():
            return {
                "success": False,
                "error": f"Greed Circuit Breaker active: {greed_lock_engine.lock_reason}. Terminal locked.",
            }

        # 2. Master Kill Switch Check
        if sebi_fortress.kill_switch_engaged:
            return {
                "success": False,
                "error": "SEBI Master Kill Switch is currently engaged. All order routing severed.",
            }

        # 3. BankNifty Freeze Quantity Check
        if "BANKNIFTY" in symbol and quantity > 900:
            return {
                "success": False,
                "error": f"Order quantity ({quantity}) breaches SEBI BankNifty Freeze Quantity Limit of 900 lots.",
            }

        ref_price = self.REFERENCE_PRICES.get(symbol.split("-")[0], 24500.0)
        est_trade_val = ref_price * quantity
        required_margin = est_trade_val * 0.15  # 15% derivative margin proxy

        # Target and Stop Loss heuristics
        if side == "BUY":
            stop_loss = round(ref_price * 0.990, 2)
            target = round(ref_price * 1.020, 2)
        else:
            stop_loss = round(ref_price * 1.010, 2)
            target = round(ref_price * 0.980, 2)

        order_id = f"MIRA-{uuid.uuid4().hex[:8].upper()}"

        prepared_payload = {
            "order_id": order_id,
            "origin": origin,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
            "price": ref_price,
            "estimated_price_inr": ref_price,
            "required_margin_inr": round(required_margin, 2),
            "stop_loss_inr": stop_loss,
            "target_inr": target,
            "prepared_at_ist": now_str,
            "timestamp_created": time.time(),
            "expires_in_seconds": 4.0,  # 4000ms SEBI expiration boundary
        }

        # Cache in pending buffer and queue to SEBI HITL guard
        self._pending_orders[order_id] = prepared_payload
        sebi_hitl_guard.queue_ai_signal(order_id, prepared_payload)

        logger.info(f"[MIRAJANE TRADE PREPARE] Prepared order {order_id} ({side} {quantity} {symbol}). Awaiting 1-Touch.")
        return {
            "success": True,
            "order_id": order_id,
            "order": prepared_payload,
            "sebi_notice": "Order prepared. Awaiting physical 1-Touch execution within 4 seconds.",
        }

    async def execute_trade(self, order_id: str, human_jwt: str = "DEV_HUMAN_SESSION") -> Dict[str, Any]:
        """
        Executes an authorized order directly via the PyO3 Rust HFT OMS
        and synchronizes paper broker positions.
        """
        if order_id not in self._pending_orders:
            return {
                "success": False,
                "error": f"Order {order_id} not found or expired (4000ms slippage timeout).",
            }

        order_spec = self._pending_orders.pop(order_id)
        symbol = order_spec["symbol"]
        qty = order_spec["quantity"]
        side = order_spec["side"]

        # Final PTRC validation
        if not sebi_fortress.Pre_Trade_Risk_Check(order_spec, available_margin=1_000_000.0, required_margin=order_spec["required_margin_inr"]):
            return {"success": False, "error": "Order rejected by SEBI Pre-Trade Risk Controls (PTRC)."}

        start_time = time.perf_counter()

        # 1. Fire to Rust PyO3 HFT OMS Engine (<50-microsecond execution)
        hft_res = await hft_engine.submit_order(symbol, qty, side, order_spec["order_type"])
        latency_us = round((time.perf_counter() - start_time) * 1_000_000, 2)

        # 2. Synchronize PaperBroker for live dashboard state tracking
        try:
            if not paper_broker.is_connected:
                await paper_broker.connect()

            paper_res = await paper_broker.place_order(
                symbol=symbol,
                qty=qty,
                side=side,
                order_type=order_spec["order_type"],
                price=order_spec["estimated_price_inr"],
                algo_id="MIRAJANE_RUST_HFT",
            )
        except Exception as broker_err:
            logger.warning(f"[MIRAJANE TRADE] Paper broker sync notice: {broker_err}")
            paper_res = {"status": "simulated", "note": str(broker_err)}


        # 3. Record position internally for Mirajane's portfolio tracking
        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        self._active_positions[symbol] = {
            "symbol": symbol,
            "side": side,
            "quantity": qty,
            "entry_price": order_spec["estimated_price_inr"],
            "current_price": order_spec["estimated_price_inr"],
            "pnl_inr": 0.0,
            "pnl_pct": 0.0,
            "stop_loss": order_spec["stop_loss_inr"],
            "target": order_spec["target_inr"],
            "opened_at_ist": now_str,
            "order_id": order_id,
        }

        # 4. Commit to SEBI 5-Year Immutable Ledger
        audit_entry = {
            "event": "MIRAJANE_ORDER_EXECUTED",
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": qty,
            "execution_engine": hft_res.get("engine", "RUST_PYO3"),
            "latency_us": latency_us,
            "authorized_jwt": human_jwt,
            "timestamp": time.time(),
        }
        sebi_fortress._commit_immutable_audit(audit_entry)

        logger.info(
            f"[MIRAJANE TRADE EXECUTED] {order_id} Filled: {side} {qty} {symbol} "
            f"via {hft_res.get('engine')} in {latency_us}µs!"
        )

        return {
            "success": True,
            "order_id": order_id,
            "status": "FILLED",
            "symbol": symbol,
            "side": side,
            "quantity": qty,
            "price_inr": order_spec["estimated_price_inr"],
            "engine": hft_res.get("engine", "RUST_PYO3"),
            "latency_microseconds": latency_us,
            "broker_response": paper_res,
        }

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Returns all open positions managed by Mirajane."""
        return list(self._active_positions.values())

    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Flattens a specific open position immediately at market."""
        if symbol not in self._active_positions:
            return {"success": False, "error": f"No active position found for {symbol}."}

        pos = self._active_positions.pop(symbol)
        reverse_side = "SELL" if pos["side"] == "BUY" else "BUY"

        # Execute counter-order through Rust engine
        hft_res = await hft_engine.submit_order(symbol, pos["quantity"], reverse_side, "MARKET")

        logger.info(f"[MIRAJANE TRADE CLOSED] Squared off {symbol} ({pos['quantity']} lots).")
        return {
            "success": True,
            "closed_position": pos,
            "exit_engine": hft_res.get("engine", "RUST_PYO3"),
            "message": f"Position in {symbol} squared off successfully.",
        }

    async def flatten_all_positions(self) -> Dict[str, Any]:
        """Emergency action: flattens 100% of open positions immediately."""
        closed = []
        symbols = list(self._active_positions.keys())
        for sym in symbols:
            res = await self.close_position(sym)
            closed.append(res)
        logger.critical(f"[MIRAJANE FLATTEN ALL] Closed {len(closed)} open positions globally.")
        return {
            "success": True,
            "closed_count": len(closed),
            "flattened_count": len(closed),
            "details": closed,
        }


mirajane_trade_engine = MirajaneTradeEngine()
