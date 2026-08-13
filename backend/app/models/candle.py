"""
BETHBot — Candle (OHLCV) ORM model.

Stores historical and real-time candlestick data in PostgreSQL/SQLite.
Composite unique constraint on (symbol, timeframe, open_time) prevents duplicate candles.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CandleModel(Base):
    """OHLCV candlestick bar ORM model."""

    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(5), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    open: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)

    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    asset = relationship("Asset", back_populates="candles", lazy="select")

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "open_time", name="uq_candle_symbol_tf_time"),
        Index("idx_candle_symbol_tf_time", "symbol", "timeframe", "open_time"),
        Index("idx_candle_symbol_tf_time_desc", "symbol", "timeframe", open_time.desc()),
    )

    def __repr__(self) -> str:
        return f"<CandleModel {self.symbol} {self.timeframe} {self.open_time} close={self.close}>"


# Backward compatibility alias
Candle = CandleModel
