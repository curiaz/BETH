"""
BETHBot — Candle (OHLCV) ORM model.

Stores historical and real-time candlestick data.
Composite unique constraint prevents duplicate candles during re-ingestion.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Candle(Base):
    """OHLCV candlestick bar."""

    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(5), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    open: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)

    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(__import__("datetime").timezone.utc),
        nullable=False,
    )

    # Relationships
    asset = relationship("Asset", back_populates="candles")

    __table_args__ = (
        UniqueConstraint("asset_id", "timeframe", "open_time", name="uq_candle_asset_tf_time"),
        Index("idx_candle_asset_tf_time", "asset_id", "timeframe", "open_time"),
    )

    def __repr__(self) -> str:
        return f"<Candle {self.asset_id} {self.timeframe} {self.open_time}>"
