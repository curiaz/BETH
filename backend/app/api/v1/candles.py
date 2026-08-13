"""
BETHBot — Candle data endpoints.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from app.core.dependencies import DBSession
from app.schemas.candle import CandleResponse

router = APIRouter()


@router.get("/{symbol}", response_model=list[CandleResponse])
async def get_candles(
    symbol: str,
    session: DBSession,
    timeframe: str = Query(default="1h", description="Candle timeframe"),
    start: datetime | None = Query(default=None, description="Start time"),
    end: datetime | None = Query(default=None, description="End time"),
    limit: int = Query(default=500, ge=1, le=5000, description="Max candles"),
) -> list:
    """Query OHLCV candle data for a symbol."""
    from sqlalchemy import select
    from app.models.asset import Asset
    from app.models.candle import Candle

    # Normalize symbol
    normalized = symbol if "/" in symbol else f"{symbol[:3]}/{symbol[3:]}" if len(symbol) > 3 else symbol

    result = await session.execute(select(Asset).where(Asset.symbol == normalized))
    asset = result.scalar_one_or_none()
    if not asset:
        return []

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

    return [
        CandleResponse(
            open_time=c.open_time,
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
            timeframe=c.timeframe,
        )
        for c in candles
    ]
