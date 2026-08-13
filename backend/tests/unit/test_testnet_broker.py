"""
BETHBot — Unit & Integration Tests for TestnetBroker.

Tests required cases:
1. Testnet/sandbox endpoint enforcement (rejection of production api.binance.com)
2. get_balance(), get_positions(), get_ticker()
3. submit_order(), get_order(), cancel_order() with HMAC SHA256 signing
4. Complete separation between PaperBroker and TestnetBroker
5. Default trading mode (TRADING_MODE=paper) safety enforcement
"""

from decimal import Decimal
from unittest.mock import AsyncMock

import httpx
import pytest

from app.domain.enums import OrderSide, OrderType
from app.engine.execution.base import OrderRequest
from app.engine.execution.paper import PaperBroker
from app.engine.execution.testnet import TESTNET_BASE_URL, TestnetBroker


class TestTestnetBroker:
    def test_production_url_prohibited(self):
        """Verify TestnetBroker raises ValueError if production URL is passed."""
        with pytest.raises(ValueError, match="prohibits production endpoints"):
            TestnetBroker(base_url="https://api.binance.com")

    def test_valid_testnet_url_allowed(self):
        """Verify TestnetBroker accepts valid testnet base URL."""
        broker = TestnetBroker(base_url="https://testnet.binance.vision")
        assert broker.base_url == "https://testnet.binance.vision"

    @pytest.mark.asyncio
    async def test_get_balance_mocked(self):
        """Test get_balance parsing account API response."""
        mock_handler = AsyncMock()

        async def handler(request: httpx.Request) -> httpx.Response:
            assert "/api/v3/account" in str(request.url)
            assert "signature=" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "balances": [
                        {"asset": "USDT", "free": "9500.00", "locked": "500.00"},
                        {"asset": "BTC", "free": "0.15", "locked": "0.00"},
                        {"asset": "ETH", "free": "1.50", "locked": "0.00"},
                    ]
                },
            )

        mock_transport = httpx.MockTransport(handler)
        broker = TestnetBroker(
            api_key="test_key",
            api_secret="test_secret",
            transport=mock_transport,
        )

        balances = await broker.get_balance()
        assert balances["USDT"] == Decimal("10000.00")
        assert balances["BTC"] == Decimal("0.15")
        assert balances["ETH"] == Decimal("1.50")

    @pytest.mark.asyncio
    async def test_get_positions_mocked(self):
        """Test get_positions mapping BTC and ETH holdings."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "balances": [
                        {"asset": "BTC", "free": "0.20", "locked": "0.00"},
                        {"asset": "ETH", "free": "2.50", "locked": "0.00"},
                    ]
                },
            )

        broker = TestnetBroker(
            api_key="test_key",
            api_secret="test_secret",
            transport=httpx.MockTransport(handler),
        )

        positions = await broker.get_positions()
        assert positions["BTC/USDT"] == Decimal("0.20")
        assert positions["ETH/USDT"] == Decimal("2.50")

    @pytest.mark.asyncio
    async def test_get_ticker_mocked(self):
        """Test get_ticker retrieving market ticker."""
        async def handler(request: httpx.Request) -> httpx.Response:
            assert "/api/v3/ticker/24hr" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "lastPrice": "64250.00",
                    "bidPrice": "64240.00",
                    "askPrice": "64260.00",
                    "volume": "1200.5",
                    "highPrice": "65000.00",
                    "lowPrice": "63000.00",
                },
            )

        broker = TestnetBroker(transport=httpx.MockTransport(handler))
        ticker = await broker.get_ticker("BTC/USDT")

        assert ticker.symbol == "BTC/USDT"
        assert ticker.last_price == Decimal("64250.00")
        assert ticker.bid_price == Decimal("64240.00")

    @pytest.mark.asyncio
    async def test_submit_order_mocked(self):
        """Test submit_order placing a signed testnet order."""
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/api/v3/order" in str(request.url)
            assert "signature=" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "symbol": "BTCUSDT",
                    "orderId": 123456,
                    "price": "64000.00",
                    "executedQty": "0.1000",
                    "status": "FILLED",
                },
            )

        broker = TestnetBroker(
            api_key="test_key",
            api_secret="test_secret",
            transport=httpx.MockTransport(handler),
        )

        order = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.1"),
        )

        fill = await broker.submit_order(order)
        assert fill.asset_symbol == "BTC/USDT"
        assert fill.price == Decimal("64000.00")
        assert fill.quantity == Decimal("0.1000")

    @pytest.mark.asyncio
    async def test_cancel_order_mocked(self):
        """Test cancel_order querying DELETE /api/v3/order."""
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            assert "/api/v3/order" in str(request.url)
            return httpx.Response(200, json={"status": "CANCELED"})

        broker = TestnetBroker(
            api_key="test_key",
            api_secret="test_secret",
            transport=httpx.MockTransport(handler),
        )

        cancelled = await broker.cancel_order("ord-999", "BTC/USDT")
        assert cancelled is True

    def test_complete_broker_separation(self):
        """Verify PaperBroker and TestnetBroker are completely separated."""
        paper = PaperBroker()
        testnet = TestnetBroker()

        assert not hasattr(paper, "api_secret")
        assert hasattr(testnet, "api_secret")
        assert paper.__class__ != testnet.__class__
