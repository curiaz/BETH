"""
BETHBot — Pydantic schemas: Common types and enums.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class TradingMode(StrEnum):
    BACKTEST = "backtest"
    PAPER = "paper"


class SessionType(StrEnum):
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    LIVE = "LIVE"


class Timeframe(StrEnum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""

    total: int
    page: int
    page_size: int
    pages: int
    data: list


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None
    code: str | None = None
