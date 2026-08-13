"""
BETHBot — Candle Repository.

Asynchronous SQLAlchemy repository for storing, querying, and deduplicating
historical OHLCV candle market data in PostgreSQL / SQLite.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.market_config import market_registry
from app.domain.models import Candle as CandleDomainModel
from app.models.candle import CandleModel

logger = get_logger(__name__)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime object is UTC timezone-aware."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class CandleRepository:
    """
    Asynchronous SQLAlchemy repository for OHLCV candlestick data.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_candles(
        self,
        candles: Sequence[CandleDomainModel | CandleModel],
    ) -> int:
        """
        Save a batch of candles into the database.
        Prevents duplicate insertion based on (symbol, timeframe, open_time).

        Args:
            candles: List of Candle domain models or CandleModel ORM objects

        Returns:
            Number of newly inserted candles
        """
        if not candles:
            return 0

        first = candles[0]
        symbol = market_registry.validate_symbol(first.symbol)
        timeframe = first.timeframe

        # Extract timestamps to check existing entries
        timestamps = [_ensure_utc(c.open_time) for c in candles]

        # Query existing open_times to prevent duplicate insertion
        stmt = select(CandleModel.open_time).where(
            CandleModel.symbol == symbol,
            CandleModel.timeframe == timeframe,
            CandleModel.open_time.in_(timestamps),
        )
        res = await self.session.execute(stmt)
        existing_times = {_ensure_utc(t) for t in res.scalars().all()}

        new_orm_models: list[CandleModel] = []
        for c in candles:
            norm_symbol = market_registry.validate_symbol(c.symbol)
            utc_open_time = _ensure_utc(c.open_time)

            if utc_open_time in existing_times:
                continue

            # If c is an ORM instance already attached to the session, skip re-adding
            if isinstance(c, CandleModel) and c in self.session:
                continue

            utc_close_time = _ensure_utc(c.close_time)

            if isinstance(c, CandleDomainModel):
                orm_candle = CandleModel(
                    symbol=norm_symbol,
                    timeframe=c.timeframe,
                    open_time=utc_open_time,
                    close_time=utc_close_time,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume,
                )
            else:
                orm_candle = c
                orm_candle.symbol = norm_symbol
                orm_candle.open_time = utc_open_time
                orm_candle.close_time = utc_close_time

            new_orm_models.append(orm_candle)
            existing_times.add(utc_open_time)

        if not new_orm_models:
            logger.debug("candle_repo.save_skipped", symbol=symbol, count=len(candles), reason="all duplicates")
            return 0

        self.session.add_all(new_orm_models)
        await self.session.flush()

        logger.info(
            "candle_repo.saved",
            symbol=symbol,
            timeframe=timeframe,
            inserted=len(new_orm_models),
            skipped_duplicates=len(candles) - len(new_orm_models),
        )

        return len(new_orm_models)

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> list[CandleDomainModel]:
        """
        Query candles from database.

        Args:
            symbol: Trading pair symbol (e.g. "BTC/USDT", "ETH/USDT")
            timeframe: Candle interval (e.g. "1h")
            start: Start time (inclusive, UTC)
            end: End time (inclusive, UTC)
            limit: Maximum candles to return

        Returns:
            List of Candle domain models ordered chronologically by open_time
        """
        norm_symbol = market_registry.validate_symbol(symbol)

        query = (
            select(CandleModel)
            .where(
                CandleModel.symbol == norm_symbol,
                CandleModel.timeframe == timeframe,
            )
            .order_by(CandleModel.open_time.asc())
        )

        if start is not None:
            query = query.where(CandleModel.open_time >= _ensure_utc(start))
        if end is not None:
            query = query.where(CandleModel.open_time <= _ensure_utc(end))

        query = query.limit(limit)

        res = await self.session.execute(query)
        orm_candles = res.scalars().all()

        domain_candles = [
            CandleDomainModel(
                symbol=c.symbol,
                timeframe=c.timeframe,
                open_time=_ensure_utc(c.open_time),
                close_time=_ensure_utc(c.close_time) or _ensure_utc(c.open_time),
                open=c.open,
                high=c.high,
                low=c.low,
                close=c.close,
                volume=c.volume,
            )
            for c in orm_candles
        ]

        return domain_candles

    async def get_latest_candle(
        self,
        symbol: str,
        timeframe: str,
    ) -> CandleDomainModel | None:
        """
        Get the single latest candle stored for a symbol and timeframe.
        """
        norm_symbol = market_registry.validate_symbol(symbol)

        query = (
            select(CandleModel)
            .where(
                CandleModel.symbol == norm_symbol,
                CandleModel.timeframe == timeframe,
            )
            .order_by(CandleModel.open_time.desc())
            .limit(1)
        )

        res = await self.session.execute(query)
        c = res.scalar_one_or_none()

        if c is None:
            return None

        return CandleDomainModel(
            symbol=c.symbol,
            timeframe=c.timeframe,
            open_time=_ensure_utc(c.open_time),
            close_time=_ensure_utc(c.close_time) or _ensure_utc(c.open_time),
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
        )

    async def get_date_range(
        self,
        symbol: str,
        timeframe: str,
    ) -> tuple[datetime, datetime] | None:
        """
        Get earliest and latest open_time stored for a symbol and timeframe.

        Returns:
            (earliest_time, latest_time) or None if no candles exist.
        """
        norm_symbol = market_registry.validate_symbol(symbol)

        query = select(
            func.min(CandleModel.open_time),
            func.max(CandleModel.open_time),
        ).where(
            CandleModel.symbol == norm_symbol,
            CandleModel.timeframe == timeframe,
        )

        res = await self.session.execute(query)
        row = res.one_or_none()

        if row is None or row[0] is None or row[1] is None:
            return None

        return (_ensure_utc(row[0]), _ensure_utc(row[1]))
