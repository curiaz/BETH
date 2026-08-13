"""
BETHBot — Pydantic schemas: Portfolio.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PortfolioResponse(BaseModel):
    """Current portfolio state."""

    total_equity: float
    cash_balance: float
    unrealized_pnl: float
    realized_pnl: float
    positions: list[PositionSummary] = []
    session_type: str = "PAPER"


class PositionSummary(BaseModel):
    """Summary of an open position."""

    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    pnl_pct: float


class EquityPoint(BaseModel):
    """Single point on the equity curve."""

    timestamp: datetime
    equity: float


# Fix forward reference
PortfolioResponse.model_rebuild()
