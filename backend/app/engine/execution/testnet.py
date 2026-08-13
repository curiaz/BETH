"""
BETHBot — Quantara Testnet Broker Handler.

Connects strictly to Binance Spot Testnet (https://testnet.binance.vision)
for paper/sandbox testing with real exchange testnet order books.

STRICT INVARIANTS:
1. Connects ONLY to testnet/sandbox endpoints (prohibits production URLs).
2. Credentials loaded ONLY from environment variables.
3. Completely separate from PaperBroker (in-memory).
4. System default mode remains TRADING_MODE=paper.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.exceptions import ExchangeError
from app.core.logging import get_logger
from app.core.market_config import market_registry
from app.domain.models import Ticker
from app.engine.execution.base import (
    BaseExecutionHandler,
    Fill,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
)

logger = get_logger(__name__)

# Allowed Binance Testnet Base URLs
TESTNET_BASE_URL = "https://testnet.binance.vision"


class TestnetBroker(BaseExecutionHandler):
    """
    Quantara Binance Testnet Broker.

    Interacts strictly with Binance Spot Testnet endpoints for paper/sandbox order simulation.
    Does NOT connect to production trading endpoints under any circumstances.
    """

    __test__ = False

    def __init__(
        self,
        base_url: str = TESTNET_BASE_URL,
        api_key: str | None = None,
        api_secret: str | None = None,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        # 1. Endpoint safety validation
        clean_url = base_url.rstrip("/")
        if "api.binance.com" in clean_url or "testnet" not in clean_url:
            raise ValueError(
                f"Invalid testnet URL '{clean_url}'. "
                f"TestnetBroker prohibits production endpoints. Must use '{TESTNET_BASE_URL}'."
            )

        self.base_url = clean_url
        self.api_key = api_key or getattr(settings, "binance_api_key", "")
        self.api_secret = api_secret or getattr(settings, "binance_api_secret", "")
        self._timeout = timeout

        headers = {"X-MBX-APIKEY": self.api_key} if self.api_key else {}
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )

    def _sign(self, params: dict[str, Any]) -> dict[str, Any]:
        """Sign request parameters using HMAC SHA256 with api_secret."""
        if not self.api_secret:
            raise ValueError("Testnet API secret is required for signed requests.")

        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        params["signature"] = signature
        return params

    async def get_balance(self) -> dict[str, Decimal]:
        """
        Fetch testnet account asset balances from GET /api/v3/account.
        """
        try:
            params = self._sign({})
            response = await self._client.get("/api/v3/account", params=params)
            if response.status_code != 200:
                raise ExchangeError("testnet", f"Failed to fetch account balance: HTTP {response.status_code}")

            data = response.json()
            balances: dict[str, Decimal] = {}
            for item in data.get("balances", []):
                asset = item["asset"]
                free = Decimal(str(item["free"]))
                locked = Decimal(str(item["locked"]))
                if free > 0 or locked > 0:
                    balances[asset] = free + locked

            return balances
        except httpx.RequestError as e:
            logger.error("testnet_broker.get_balance_error", error=str(e))
            raise ExchangeError("testnet", f"Network error fetching testnet balances: {e}") from e

    async def get_positions(self) -> dict[str, Decimal]:
        """
        Fetch open asset positions for supported markets (e.g. BTC, ETH).
        """
        balances = await self.get_balance()
        positions: dict[str, Decimal] = {}

        if "BTC" in balances:
            positions["BTC/USDT"] = balances["BTC"]
        if "ETH" in balances:
            positions["ETH/USDT"] = balances["ETH"]

        return positions

    async def get_ticker(self, symbol: str) -> Ticker:
        """
        Fetch current testnet ticker price for symbol.
        """
        norm_symbol = market_registry.validate_symbol(symbol)
        raw_symbol = norm_symbol.replace("/", "").upper()

        try:
            response = await self._client.get("/api/v3/ticker/24hr", params={"symbol": raw_symbol})
            if response.status_code != 200:
                raise ExchangeError("testnet", f"Failed to fetch ticker for {norm_symbol}: HTTP {response.status_code}")

            data = response.json()
            return Ticker(
                symbol=norm_symbol,
                last_price=Decimal(data["lastPrice"]),
                bid_price=Decimal(data["bidPrice"]),
                ask_price=Decimal(data["askPrice"]),
                volume_24h=Decimal(data["volume"]),
                high_24h=Decimal(data["highPrice"]),
                low_24h=Decimal(data["lowPrice"]),
                timestamp=datetime.now(timezone.utc),
            )
        except httpx.RequestError as e:
            logger.error("testnet_broker.get_ticker_error", symbol=norm_symbol, error=str(e))
            raise ExchangeError("testnet", f"Network error fetching ticker for {norm_symbol}: {e}") from e

    async def submit_order(self, order: OrderRequest) -> Fill:
        """
        Submit a testnet order to POST /api/v3/order.
        """
        norm_symbol = market_registry.validate_symbol(order.asset_symbol)
        raw_symbol = norm_symbol.replace("/", "").upper()

        params: dict[str, Any] = {
            "symbol": raw_symbol,
            "side": order.side.value,
            "type": order.order_type.value,
            "quantity": str(order.quantity),
            "newClientOrderId": order.id,
        }

        if order.order_type == OrderType.LIMIT:
            if order.price is None or order.price <= 0:
                raise ValueError("Limit order requires positive price.")
            params["price"] = str(order.price)
            params["timeInForce"] = order.time_in_force

        signed_params = self._sign(params)

        try:
            response = await self._client.post("/api/v3/order", params=signed_params)
            if response.status_code != 200:
                body = response.text[:200]
                raise ExchangeError("testnet", f"Testnet order placement failed (HTTP {response.status_code}): {body}")

            data = response.json()
            fill_price = Decimal(data.get("price", "0.0"))
            if fill_price == 0 and "cummulativeQuoteQty" in data and "executedQty" in data:
                exec_qty = Decimal(data["executedQty"])
                if exec_qty > 0:
                    fill_price = Decimal(data["cummulativeQuoteQty"]) / exec_qty
                else:
                    ticker = await self.get_ticker(norm_symbol)
                    fill_price = ticker.last_price

            fee = fill_price * order.quantity * Decimal("0.001")  # Default 0.1% testnet fee

            fill = Fill(
                order_id=order.id,
                asset_symbol=norm_symbol,
                side=order.side,
                quantity=Decimal(data.get("executedQty", str(order.quantity))),
                price=fill_price,
                fee=fee,
                slippage=Decimal("0.0"),
                timestamp=datetime.now(timezone.utc),
                status=OrderStatus.FILLED if data.get("status") in ("FILLED", "NEW") else OrderStatus.PENDING,
            )

            logger.info(
                "testnet_broker.order_submitted",
                symbol=norm_symbol,
                side=order.side.value,
                order_id=order.id,
                price=str(fill_price),
            )
            return fill

        except httpx.RequestError as e:
            logger.error("testnet_broker.submit_order_error", symbol=norm_symbol, error=str(e))
            raise ExchangeError("testnet", f"Network error submitting testnet order for {norm_symbol}: {e}") from e

    async def get_order(self, order_id: str, symbol: str) -> dict[str, Any]:
        """
        Query a testnet order status via GET /api/v3/order.
        """
        norm_symbol = market_registry.validate_symbol(symbol)
        raw_symbol = norm_symbol.replace("/", "").upper()

        params = self._sign({"symbol": raw_symbol, "origClientOrderId": order_id})

        try:
            response = await self._client.get("/api/v3/order", params=params)
            if response.status_code != 200:
                raise ExchangeError("testnet", f"Query order failed (HTTP {response.status_code}): {response.text[:200]}")
            return response.json()
        except httpx.RequestError as e:
            logger.error("testnet_broker.get_order_error", order_id=order_id, error=str(e))
            raise ExchangeError("testnet", f"Network error querying testnet order: {e}") from e

    async def cancel_order(self, order_id: str, symbol: str = "BTC/USDT") -> bool:
        """
        Cancel a pending testnet order via DELETE /api/v3/order.
        """
        norm_symbol = market_registry.validate_symbol(symbol)
        raw_symbol = norm_symbol.replace("/", "").upper()

        params = self._sign({"symbol": raw_symbol, "origClientOrderId": order_id})

        try:
            response = await self._client.delete("/api/v3/order", params=params)
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.error("testnet_broker.cancel_order_error", order_id=order_id, error=str(e))
            return False

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Query status mapping."""
        return OrderStatus.FILLED

    async def close(self) -> None:
        """Close client transport."""
        await self._client.aclose()
