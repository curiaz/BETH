"""
BETHBot — Market data service.

Fetches OHLCV data from exchange, stores in database, and serves queries.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.integrations.exchange.base import ExchangeAdapter
from app.models.asset import Asset
from app.models.candle import Candle

logger = get_logger(__name__)


class MarketDataService:
    """Fetches, stores, and queries OHLCV market data."""

    def __init__(self, exchange: ExchangeAdapter):
        self._exchange = exchange

    async def fetch_and_store(
        self,
        session: AsyncSession,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> int:
        """
        Fetch candles from exchange and store in database.
        Returns the number of new candles stored.
        """
        # Get asset
        result = await session.execute(select(Asset).where(Asset.symbol == symbol))
        asset = result.scalar_one_or_none()
        if not asset:
            logger.warning("market_data.asset_not_found", symbol=symbol)
            return 0

        # Fetch from exchange
        df = await self._exchange.fetch_ohlcv(symbol, timeframe, start, end, limit)
        if df.empty:
            return 0

        count = 0
        for open_time, row in df.iterrows():
            # Check for existing candle
            existing = await session.execute(
                select(Candle).where(
                    Candle.asset_id == asset.id,
                    Candle.timeframe == timeframe,
                    Candle.open_time == open_time.to_pydatetime() if hasattr(open_time, 'to_pydatetime') else open_time,
                )
            )
            if existing.scalar_one_or_none():
                continue

            candle = Candle(
                asset_id=asset.id,
                timeframe=timeframe,
                open_time=open_time.to_pydatetime() if hasattr(open_time, 'to_pydatetime') else open_time,
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=Decimal(str(row["volume"])),
                close_time=row.get("close_time").to_pydatetime() if "close_time" in row and hasattr(row.get("close_time"), 'to_pydatetime') else None,
            )
            session.add(candle)
            count += 1

        await session.flush()
        logger.info(
            "market_data.stored",
            symbol=symbol,
            timeframe=timeframe,
            new_candles=count,
        )
        return count

    async def get_candles(
        self,
        session: AsyncSession,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 500,
    ) -> pd.DataFrame:
        """
        Query candles from database and return as DataFrame.
        """
        result = await session.execute(select(Asset).where(Asset.symbol == symbol))
        asset = result.scalar_one_or_none()
        if not asset:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        query = (
            select(Candle)
            .where(Candle.asset_id == asset.id, Candle.timeframe == timeframe)
            .order_by(Candle.open_time)
        )

        if start:
            query = query.where(Candle.open_time >= start)
        if end:
            query = query.where(Candle.open_time <= end)

        query = query.limit(limit)

        result = await session.execute(query)
        candles = result.scalars().all()

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
