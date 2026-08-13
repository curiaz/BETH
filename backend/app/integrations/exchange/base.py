"""
BETHBot — Market Data Provider Interface.

Abstract base class for all exchange market data providers.
All market data consumers depend on this abstraction, not directly on exchange clients.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

import pandas as pd

from app.domain.models import Candle, Ticker


class MarketDataProvider(ABC):
    """
    Abstract market data provider interface.

    Isolates exchange REST/WebSocket APIs behind a clean contract.
    Provides historical OHLCV candlestick data and real-time ticker snapshots.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange name (e.g., 'binance')."""
        ...

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV candlestick data.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT", "ETH/USDT")
            timeframe: Candle interval (e.g., "1m", "5m", "15m", "1h", "4h", "1d")
            start: Start timestamp (inclusive, UTC)
            end: End timestamp (inclusive, optional, UTC)
            limit: Maximum candles to return per request

        Returns:
            DataFrame indexed by DatetimeIndex (open_time, UTC) with columns:
            [open, high, low, close, volume] using Decimal or float types.
        """
        ...

    @abstractmethod
    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> list[Candle]:
        """
        Fetch historical candles as a list of validated domain Candle objects.
        """
        ...

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        Get the current price ticker snapshot for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")

        Returns:
            Validated Ticker domain model
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close HTTP connections and release resources."""
        ...


# Backward compatibility alias
ExchangeAdapter = MarketDataProvider
