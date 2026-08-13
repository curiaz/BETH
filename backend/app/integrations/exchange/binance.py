"""
BETHBot — Binance exchange adapter.

Implements ExchangeAdapter for Binance REST API.
Phase 1: Data-only (OHLCV, ticker, exchange info). No order submission.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pandas as pd

from app.core.logging import get_logger
from app.integrations.exchange.base import ExchangeAdapter

logger = get_logger(__name__)

# Binance timeframe mapping
TIMEFRAME_MAP = {
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


def _symbol_to_binance(symbol: str) -> str:
    """Convert 'BTC/USDT' to 'BTCUSDT'."""
    return symbol.replace("/", "")


class BinanceAdapter(ExchangeAdapter):
    """
    Binance REST API adapter using httpx.

    Uses public endpoints only — API key is optional for OHLCV and ticker.
    """

    BASE_URL = "https://api.binance.com"

    def __init__(self, api_key: str = "", api_secret: str = ""):
        self._api_key = api_key
        self._api_secret = api_secret

        headers = {}
        if api_key:
            headers["X-MBX-APIKEY"] = api_key

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=httpx.Timeout(30.0),
        )

    @property
    def name(self) -> str:
        return "binance"

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Binance /api/v3/klines."""
        binance_symbol = _symbol_to_binance(symbol)
        binance_interval = TIMEFRAME_MAP.get(timeframe, timeframe)

        params: dict = {
            "symbol": binance_symbol,
            "interval": binance_interval,
            "startTime": int(start.timestamp() * 1000),
            "limit": min(limit, 1000),  # Binance max is 1000
        }
        if end:
            params["endTime"] = int(end.timestamp() * 1000)

        logger.debug(
            "binance.fetch_ohlcv",
            symbol=symbol,
            timeframe=timeframe,
            start=start.isoformat(),
        )

        response = await self._client.get("/api/v3/klines", params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        # Binance klines format:
        # [open_time, open, high, low, close, volume, close_time, ...]
        records = []
        for candle in data:
            records.append({
                "open_time": pd.Timestamp(candle[0], unit="ms", tz="UTC"),
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "close_time": pd.Timestamp(candle[6], unit="ms", tz="UTC"),
            })

        df = pd.DataFrame(records)
        df.set_index("open_time", inplace=True)

        logger.info(
            "binance.ohlcv_fetched",
            symbol=symbol,
            timeframe=timeframe,
            candles=len(df),
        )

        return df

    async def get_ticker_price(self, symbol: str) -> Decimal:
        """Fetch current price from Binance /api/v3/ticker/price."""
        binance_symbol = _symbol_to_binance(symbol)

        response = await self._client.get(
            "/api/v3/ticker/price",
            params={"symbol": binance_symbol},
        )
        response.raise_for_status()
        data = response.json()

        return Decimal(data["price"])

    async def get_exchange_info(self, symbol: str) -> dict:
        """Fetch symbol info from Binance /api/v3/exchangeInfo."""
        binance_symbol = _symbol_to_binance(symbol)

        response = await self._client.get(
            "/api/v3/exchangeInfo",
            params={"symbol": binance_symbol},
        )
        response.raise_for_status()
        data = response.json()

        # Parse filters for the symbol
        result: dict = {
            "tick_size": "0.01",
            "lot_size": "0.00001",
            "min_notional": "10.0",
        }

        for sym_info in data.get("symbols", []):
            if sym_info["symbol"] == binance_symbol:
                for f in sym_info.get("filters", []):
                    if f["filterType"] == "PRICE_FILTER":
                        result["tick_size"] = f["tickSize"]
                    elif f["filterType"] == "LOT_SIZE":
                        result["lot_size"] = f["stepSize"]
                    elif f["filterType"] == "NOTIONAL":
                        result["min_notional"] = f.get("minNotional", "10.0")
                    elif f["filterType"] == "MIN_NOTIONAL":
                        result["min_notional"] = f.get("minNotional", "10.0")
                break

        return result

    async def close(self) -> None:
        """Close the httpx client."""
        await self._client.aclose()
