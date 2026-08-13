"""
BETHBot — Binance Market Data Provider.

Implements MarketDataProvider for Binance public REST API endpoints.
Provides historical OHLCV data retrieval, symbol normalization, timestamp cleaning,
duplicate detection, missing candle gap detection, and error logging.
No API keys required for public market data.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
import pandas as pd

from app.core.exceptions import ExchangeError, InvalidSymbolError
from app.core.logging import get_logger
from app.core.market_config import market_registry
from app.domain.models import Candle, Ticker
from app.integrations.exchange.base import MarketDataProvider

logger = get_logger(__name__)

# Timeframe interval string to timedelta mapping
TIMEFRAME_DELTAS: dict[str, timedelta] = {
    "1m": timedelta(minutes=1),
    "3m": timedelta(minutes=3),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "2h": timedelta(hours=2),
    "4h": timedelta(hours=4),
    "6h": timedelta(hours=6),
    "8h": timedelta(hours=8),
    "12h": timedelta(hours=12),
    "1d": timedelta(days=1),
    "3d": timedelta(days=3),
    "1w": timedelta(weeks=1),
}

# Binance interval parameter mapping
BINANCE_INTERVAL_MAP = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "8h": "8h",
    "12h": "12h",
    "1d": "1d",
    "3d": "3d",
    "1w": "1w",
    "1M": "1M",
}


def _symbol_to_binance_raw(symbol: str) -> str:
    """Convert standard 'BTC/USDT' symbol to Binance 'BTCUSDT' format."""
    return symbol.replace("/", "").upper()


class BinanceMarketDataProvider(MarketDataProvider):
    """
    Binance REST API implementation of MarketDataProvider.

    Data-only: retrieves historical OHLCV data and real-time ticker prices.
    No order placement or trading execution is implemented.
    """

    DEFAULT_BASE_URL = "https://api.binance.com"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )

    @property
    def name(self) -> str:
        return "binance"

    async def get_ticker(self, symbol: str) -> Ticker:
        """
        Fetch current ticker snapshot for symbol from Binance /api/v3/ticker/price
        and /api/v3/ticker/24hr.
        """
        norm_symbol = market_registry.validate_symbol(symbol)
        raw_symbol = _symbol_to_binance_raw(norm_symbol)

        try:
            response = await self._client.get(
                "/api/v3/ticker/24hr",
                params={"symbol": raw_symbol},
            )
            if response.status_code != 200:
                self._handle_api_error_response(response, norm_symbol)

            data = response.json()
            last_price = Decimal(data["lastPrice"])
            bid_price = Decimal(data["bidPrice"])
            ask_price = Decimal(data["askPrice"])
            volume_24h = Decimal(data["volume"])
            high_24h = Decimal(data["highPrice"])
            low_24h = Decimal(data["lowPrice"])

            return Ticker(
                symbol=norm_symbol,
                last_price=last_price,
                bid_price=bid_price,
                ask_price=ask_price,
                volume_24h=volume_24h,
                high_24h=high_24h,
                low_24h=low_24h,
                timestamp=datetime.now(timezone.utc),
            )

        except httpx.TimeoutException as e:
            logger.error("binance.ticker_timeout", symbol=norm_symbol, timeout=self._timeout)
            raise ExchangeError("binance", f"Network timeout fetching ticker for {norm_symbol}") from e

        except httpx.RequestError as e:
            logger.error("binance.ticker_network_error", symbol=norm_symbol, error=str(e))
            raise ExchangeError("binance", f"Network connection error fetching ticker for {norm_symbol}: {e}") from e

        except (KeyError, ValueError, InvalidOperation) as e:
            logger.error("binance.ticker_invalid_data", symbol=norm_symbol, error=str(e))
            raise ExchangeError("binance", f"Received malformed ticker data for {norm_symbol}: {e}") from e

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> list[Candle]:
        """
        Fetch historical candles from Binance /api/v3/klines and return as
        validated, cleaned Candle domain models.
        """
        norm_symbol = market_registry.validate_symbol(symbol)
        raw_symbol = _symbol_to_binance_raw(norm_symbol)
        interval = BINANCE_INTERVAL_MAP.get(timeframe, timeframe)

        start_ms = int(start.timestamp() * 1000)
        params: dict[str, Any] = {
            "symbol": raw_symbol,
            "interval": interval,
            "startTime": start_ms,
            "limit": min(limit, 1000),
        }
        if end is not None:
            params["endTime"] = int(end.timestamp() * 1000)

        logger.info(
            "binance.fetch_klines_request",
            symbol=norm_symbol,
            timeframe=timeframe,
            start=start.isoformat(),
        )

        try:
            response = await self._client.get("/api/v3/klines", params=params)
            if response.status_code != 200:
                self._handle_api_error_response(response, norm_symbol)

            raw_klines = response.json()

        except httpx.TimeoutException as e:
            logger.error("binance.klines_timeout", symbol=norm_symbol, timeout=self._timeout)
            raise ExchangeError("binance", f"Network timeout fetching candles for {norm_symbol}") from e

        except httpx.RequestError as e:
            logger.error("binance.klines_network_error", symbol=norm_symbol, error=str(e))
            raise ExchangeError("binance", f"Network error fetching candles for {norm_symbol}: {e}") from e

        if not isinstance(raw_klines, list):
            logger.error("binance.klines_malformed_response", symbol=norm_symbol, type=type(raw_klines).__name__)
            raise ExchangeError("binance", f"Expected list of klines from Binance, got {type(raw_klines).__name__}")

        candles = self._parse_and_validate_klines(raw_klines, norm_symbol, timeframe)
        return candles

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data and return as a pandas DataFrame indexed by open_time.
        """
        candles = await self.fetch_candles(symbol, timeframe, start, end, limit)

        if not candles:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        records = [
            {
                "open_time": c.open_time,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume),
            }
            for c in candles
        ]

        df = pd.DataFrame(records)
        df.set_index("open_time", inplace=True)
        return df

    def _parse_and_validate_klines(
        self,
        raw_klines: list[list],
        symbol: str,
        timeframe: str,
    ) -> list[Candle]:
        """
        Parse raw Binance klines, detect duplicates, detect missing gaps,
        validate OHLC rules, and construct Candle domain objects.
        """
        if not raw_klines:
            logger.warning("binance.klines_empty_result", symbol=symbol)
            return []

        parsed_candles: list[Candle] = []
        seen_timestamps: set[datetime] = set()
        duplicate_count = 0

        for item in raw_klines:
            if not isinstance(item, list) or len(item) < 7:
                logger.warning("binance.kline_item_invalid", symbol=symbol, item=item)
                continue

            try:
                open_time_ms = int(item[0])
                open_time = datetime.fromtimestamp(open_time_ms / 1000.0, tz=timezone.utc)
                close_time_ms = int(item[6])
                close_time = datetime.fromtimestamp(close_time_ms / 1000.0, tz=timezone.utc)

                # Duplicate Timestamp Detection
                if open_time in seen_timestamps:
                    duplicate_count += 1
                    logger.warning(
                        "binance.duplicate_timestamp_detected",
                        symbol=symbol,
                        timestamp=open_time.isoformat(),
                    )
                    continue
                seen_timestamps.add(open_time)

                open_price = Decimal(str(item[1]))
                high_price = Decimal(str(item[2]))
                low_price = Decimal(str(item[3]))
                close_price = Decimal(str(item[4]))
                volume = Decimal(str(item[5]))

                candle = Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time=open_time,
                    close_time=close_time,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                )
                parsed_candles.append(candle)

            except (ValueError, InvalidOperation, TypeError) as e:
                logger.warning("binance.kline_parse_error", symbol=symbol, item=item, error=str(e))
                continue

        # Sort candles chronologically by open_time
        parsed_candles.sort(key=lambda c: c.open_time)

        # Missing Candle Gap Detection
        if len(parsed_candles) > 1 and timeframe in TIMEFRAME_DELTAS:
            expected_delta = TIMEFRAME_DELTAS[timeframe]
            missing_gaps = 0

            for i in range(len(parsed_candles) - 1):
                t1 = parsed_candles[i].open_time
                t2 = parsed_candles[i + 1].open_time
                gap = t2 - t1

                if gap > expected_delta:
                    missing_count = int(gap / expected_delta) - 1
                    missing_gaps += missing_count
                    logger.warning(
                        "binance.missing_candles_detected",
                        symbol=symbol,
                        timeframe=timeframe,
                        start_gap=t1.isoformat(),
                        end_gap=t2.isoformat(),
                        missing_count=missing_count,
                    )

            if missing_gaps > 0:
                logger.info(
                    "binance.gap_summary",
                    symbol=symbol,
                    total_missing_candles=missing_gaps,
                )

        logger.info(
            "binance.parsed_candles_success",
            symbol=symbol,
            valid_candles=len(parsed_candles),
            duplicates_dropped=duplicate_count,
        )

        return parsed_candles

    def _handle_api_error_response(self, response: httpx.Response, symbol: str) -> None:
        """Parse error payload from non-200 HTTP responses and raise ExchangeError."""
        error_msg = f"HTTP {response.status_code}"
        try:
            body = response.json()
            if isinstance(body, dict) and "msg" in body:
                error_msg = f"Code {body.get('code')}: {body.get('msg')}"
        except Exception:
            error_msg = response.text[:200]

        logger.error(
            "binance.api_error_response",
            symbol=symbol,
            status_code=response.status_code,
            error=error_msg,
        )
        raise ExchangeError("binance", f"Binance API error for {symbol} ({error_msg})")

    async def get_ticker_price(self, symbol: str) -> Decimal:
        """Get current ticker price as Decimal."""
        ticker = await self.get_ticker(symbol)
        return ticker.last_price

    async def get_exchange_info(self, symbol: str) -> dict:
        """Get market info for symbol."""
        market = market_registry.get_market(symbol)
        return {
            "tick_size": str(market.tick_size),
            "lot_size": str(market.lot_size),
            "min_notional": str(market.min_notional),
            "maker_fee": str(market.maker_fee),
            "taker_fee": str(market.taker_fee),
        }

    async def close(self) -> None:
        """Close client resources."""
        await self._client.aclose()


# Backward compatibility alias
BinanceAdapter = BinanceMarketDataProvider
