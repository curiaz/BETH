"""
BETHBot — Pydantic schemas: Candle.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CandleResponse(BaseModel):
    """Candle response schema."""

    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    timeframe: str

    model_config = {"from_attributes": True}


class CandleQuery(BaseModel):
    """Query parameters for candle data."""

    symbol: str
    timeframe: str = "1h"
    start: datetime | None = None
    end: datetime | None = None
    limit: int = Field(default=500, ge=1, le=5000)
