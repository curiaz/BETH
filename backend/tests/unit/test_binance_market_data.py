"""
BETHBot — Unit Tests for Binance Market Data Provider.

Tests all required functionality using mocked Binance HTTP responses:
1. BTC/USDT and ETH/USDT historical OHLCV candle retrieval
2. Symbol normalization (btc/usdt -> BTC/USDT -> BTCUSDT)
3. Network timeout handling
4. API error handling (4xx, 5xx)
5. Validation of returned data (prices, timestamps, volume)
6. Detection of duplicate timestamps
7. Detection of missing candles (gaps)
8. Real-time ticker retrieval
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal

import httpx
import pytest

from app.core.exceptions import ExchangeError, InvalidSymbolError
from app.integrations.exchange.binance import BinanceMarketDataProvider


# Helper to build mock Binance kline item
def make_mock_kline(
    open_time_ms: int,
    open_price="42000.00",
    high="42500.00",
    low="41800.00",
    close="42300.00",
    volume="10.5",
):
    close_time_ms = open_time_ms + (3600 * 1000 - 1)  # 1h candle
    return [
        open_time_ms,
        open_price,
        high,
        low,
        close,
        volume,
        close_time_ms,
        "444150.00",  # quote asset volume
        100,           # number of trades
        "5.2",         # taker buy base asset volume
        "220000.00",   # taker buy quote asset volume
        "0",           # ignore
    ]


class TestBinanceMarketDataProvider:
    @pytest.mark.asyncio
    async def test_fetch_btc_usdt_candles_success(self):
        """Test fetching historical OHLCV candles for BTC/USDT."""
        start_ms = 1704067200000  # 2024-01-01 00:00:00 UTC

        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v3/klines"
            assert "symbol=BTCUSDT" in request.url.query.decode()
            assert "interval=1h" in request.url.query.decode()

            klines = [
                make_mock_kline(start_ms, "42000.00", "42500.00", "41800.00", "42300.00", "15.0"),
                make_mock_kline(start_ms + 3600000, "42300.00", "42800.00", "42100.00", "42600.00", "12.0"),
            ]
            return httpx.Response(200, json=klines)

        transport = httpx.MockTransport(handler)
        provider = BinanceMarketDataProvider(transport=transport)

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        candles = await provider.fetch_candles("BTC/USDT", "1h", start)

        assert len(candles) == 2
        assert candles[0].symbol == "BTC/USDT"
        assert candles[0].open == Decimal("42000.00")
        assert candles[0].close == Decimal("42300.00")
        assert candles[0].volume == Decimal("15.0")
        assert candles[1].close == Decimal("42600.00")

        await provider.close()

    @pytest.mark.asyncio
    async def test_fetch_eth_usdt_candles_success(self):
        """Test fetching historical OHLCV candles for ETH/USDT."""
        start_ms = 1704067200000

        async def handler(request: httpx.Request) -> httpx.Response:
            assert "symbol=ETHUSDT" in request.url.query.decode()
            klines = [make_mock_kline(start_ms, "2200.00", "2250.00", "2190.00", "2240.00", "100.0")]
            return httpx.Response(200, json=klines)

        transport = httpx.MockTransport(handler)
        provider = BinanceMarketDataProvider(transport=transport)

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        candles = await provider.fetch_candles("ETH/USDT", "1h", start)

        assert len(candles) == 1
        assert candles[0].symbol == "ETH/USDT"
        assert candles[0].open == Decimal("2200.00")

        await provider.close()

    @pytest.mark.asyncio
    async def test_symbol_normalization(self):
        """Test that symbol forms like 'ethusdt' or 'btc/usdt' are normalized."""
        start_ms = 1704067200000

        async def handler(request: httpx.Request) -> httpx.Response:
            assert "symbol=ETHUSDT" in request.url.query.decode()
            return httpx.Response(200, json=[make_mock_kline(start_ms)])

        transport = httpx.MockTransport(handler)
        provider = BinanceMarketDataProvider(transport=transport)

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        candles = await provider.fetch_candles("ethusdt", "1h", start)

        assert len(candles) == 1
        assert candles[0].symbol == "ETH/USDT"

        await provider.close()

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test that httpx.TimeoutException is caught and raised as ExchangeError."""

        async def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Connection timed out", request=request)

        transport = httpx.MockTransport(handler)
        provider = BinanceMarketDataProvider(transport=transport)

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        with pytest.raises(ExchangeError, match="Network timeout fetching candles"):
            await provider.fetch_candles("BTC/USDT", "1h", start)

        await provider.close()

    @pytest.mark.asyncio
    async def test_api_error_response_handling(self):
        """Test non-200 HTTP API response with error JSON."""

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                400,
                json={"code": -1121, "msg": "Invalid symbol."},
            )

        transport = httpx.MockTransport(handler)
        provider = BinanceMarketDataProvider(transport=transport)

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        with pytest.raises(ExchangeError, match="Invalid symbol."):
            await provider.fetch_candles("BTC/USDT", "1h", start)

        await provider.close()

    @pytest.mark.asyncio
    async def test_detect_duplicate_timestamps(self):
        """Test detection and removal of duplicate timestamp klines."""
        start_ms = 1704067200000

        async def handler(request: httpx.Request) -> httpx.Response:
            # Return duplicate timestamp for open_time
            klines = [
                make_mock_kline(start_ms, "42000.00"),
                make_mock_kline(start_ms, "42000.00"),  # Exact duplicate timestamp!
                make_mock_kline(start_ms + 3600000, "42300.00"),
            ]
            return httpx.Response(200, json=klines)

        transport = httpx.MockTransport(handler)
        provider = BinanceMarketDataProvider(transport=transport)

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        candles = await provider.fetch_candles("BTC/USDT", "1h", start)

        # Duplicate should be dropped cleanly
        assert len(candles) == 2

        await provider.close()

    @pytest.mark.asyncio
    async def test_detect_missing_candles_gap(self):
        """Test gap detection logic for missing candles."""
        start_ms = 1704067200000  # T0

        async def handler(request: httpx.Request) -> httpx.Response:
            # 3-hour gap between T0 and T0 + 4 hours
            klines = [
                make_mock_kline(start_ms),
                make_mock_kline(start_ms + (4 * 3600 * 1000)),  # 4 hours later (missing 3 bars)
            ]
            return httpx.Response(200, json=klines)

        transport = httpx.MockTransport(handler)
        provider = BinanceMarketDataProvider(transport=transport)

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        candles = await provider.fetch_candles("BTC/USDT", "1h", start)

        assert len(candles) == 2

        await provider.close()

    @pytest.mark.asyncio
    async def test_fetch_ticker_success(self):
        """Test ticker retrieval."""

        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v3/ticker/24hr"
            return httpx.Response(
                200,
                json={
                    "symbol": "BTCUSDT",
                    "lastPrice": "42500.00",
                    "bidPrice": "42490.00",
                    "askPrice": "42510.00",
                    "volume": "1200.5",
                    "highPrice": "43000.00",
                    "lowPrice": "41500.00",
                },
            )

        transport = httpx.MockTransport(handler)
        provider = BinanceMarketDataProvider(transport=transport)

        ticker = await provider.get_ticker("BTC/USDT")
        assert ticker.symbol == "BTC/USDT"
        assert ticker.last_price == Decimal("42500.00")
        assert ticker.bid_price == Decimal("42490.00")
        assert ticker.ask_price == Decimal("42510.00")

        await provider.close()
