"""
BETHBot — Ticker ORM model.

Stores ticker snapshots in the database for analytics.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TickerModel(Base):
    """Ticker ORM model for real-time market price persistence."""

    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    last_price: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    bid_price: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    ask_price: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    volume_24h: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("0")
    )

    high_24h: Mapped[Decimal | None] = mapped_column(Numeric(precision=20, scale=8), nullable=True)
    low_24h: Mapped[Decimal | None] = mapped_column(Numeric(precision=20, scale=8), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_ticker_symbol_time", "symbol", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Ticker {self.symbol} price={self.last_price} at {self.timestamp}>"
