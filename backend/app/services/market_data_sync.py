"""
BETHBot — Market Data Sync Service.

Coordinates MarketDataProvider (exchange client) and CandleRepository (database)
to synchronize historical market data efficiently without downloading duplicate data unnecessarily.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.logging import get_logger
from app.domain.models import Candle
from app.integrations.exchange.base import MarketDataProvider
from app.repositories.candle_repository import CandleRepository

logger = get_logger(__name__)


class MarketDataSyncService:
    """
    Synchronizes historical market data between external provider and local database.
    """

    def __init__(self, provider: MarketDataProvider, repository: CandleRepository):
        self.provider = provider
        self.repository = repository

    async def sync_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        """
        Synchronize candles for the specified symbol, timeframe, and date range.
        Avoids downloading data already cached in the database.

        Args:
            symbol: Trading pair symbol (e.g. "BTC/USDT", "ETH/USDT")
            timeframe: Candle interval (e.g. "1h")
            start: Start timestamp (UTC)
            end: End timestamp (UTC)

        Returns:
            Complete list of Candle domain models from database for requested range
        """
        cached_range = await self.repository.get_date_range(symbol, timeframe)

        if cached_range is None:
            # Case 1: No cached data exist — download full range
            logger.info("market_sync.full_download", symbol=symbol, timeframe=timeframe)
            fetched = await self.provider.fetch_candles(symbol, timeframe, start, end)
            if fetched:
                await self.repository.save_candles(fetched)

        else:
            earliest_cached, latest_cached = cached_range

            # Case 2: Fetch missing tail data if end > latest_cached
            if end > latest_cached:
                logger.info(
                    "market_sync.fetch_tail_gap",
                    symbol=symbol,
                    start_fetch=latest_cached.isoformat(),
                    end_fetch=end.isoformat(),
                )
                tail_candles = await self.provider.fetch_candles(
                    symbol, timeframe, start=latest_cached, end=end
                )
                if tail_candles:
                    await self.repository.save_candles(tail_candles)

            # Case 3: Fetch missing head data if start < earliest_cached
            if start < earliest_cached:
                logger.info(
                    "market_sync.fetch_head_gap",
                    symbol=symbol,
                    start_fetch=start.isoformat(),
                    end_fetch=earliest_cached.isoformat(),
                )
                head_candles = await self.provider.fetch_candles(
                    symbol, timeframe, start=start, end=earliest_cached
                )
                if head_candles:
                    await self.repository.save_candles(head_candles)

            if start >= earliest_cached and end <= latest_cached:
                logger.info("market_sync.cache_hit_skip_download", symbol=symbol, timeframe=timeframe)

        # Return full data from database
        return await self.repository.get_candles(symbol, timeframe, start, end)
