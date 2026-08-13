"""
BETHBot — Exchange adapter interface.

All exchange-specific code is isolated behind this abstraction.
Swapping Binance for Bybit requires only a new adapter implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

import pandas as pd


class ExchangeAdapter(ABC):
    """
    Abstract exchange adapter.

    Phase 1: Data-only (fetch candles, get ticker price, get exchange info).
    Phase 2+: Order submission via test/sandbox endpoints first.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange name (e.g. 'binance')."""
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
        Fetch OHLCV candlestick data.

        Args:
            symbol: Trading pair (e.g. "BTC/USDT")
            timeframe: Candle interval (e.g. "1h", "4h", "1d")
            start: Start time (inclusive)
            end: End time (inclusive, optional)
            limit: Max number of candles to fetch

        Returns:
            DataFrame with columns: [open, high, low, close, volume]
            Index: DatetimeIndex with open_time
        """
        ...

    @abstractmethod
    async def get_ticker_price(self, symbol: str) -> Decimal:
        """
        Get the current ticker price for a symbol.

        Args:
            symbol: Trading pair (e.g. "BTC/USDT")

        Returns:
            Current price as Decimal
        """
        ...

    @abstractmethod
    async def get_exchange_info(self, symbol: str) -> dict:
        """
        Get exchange-specific info for a symbol (tick size, lot size, etc.).

        Args:
            symbol: Trading pair (e.g. "BTC/USDT")

        Returns:
            Dict with keys: tick_size, lot_size, min_notional, etc.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        ...
