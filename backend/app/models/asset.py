"""
BETHBot — Asset ORM model.

Represents a tradable instrument (e.g., BTC/USDT).
Assets are configurable — not hardcoded into business logic.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Asset(Base, TimestampMixin):
    """A tradable instrument / trading pair."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    base_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False, default="binance")
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False, default="SPOT")

    # Precision rules
    tick_size: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=10), nullable=False, default=Decimal("0.01")
    )
    lot_size: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=10), nullable=False, default=Decimal("0.00001")
    )
    min_notional: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=10), nullable=False, default=Decimal("10.0")
    )

    # Fee schedule
    maker_fee: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6), nullable=False, default=Decimal("0.001")
    )
    taker_fee: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6), nullable=False, default=Decimal("0.001")
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    candles = relationship("CandleModel", back_populates="asset", lazy="select")
    signals = relationship("Signal", back_populates="asset", lazy="select")

    __table_args__ = (
        Index("idx_asset_exchange", "exchange"),
    )

    def __repr__(self) -> str:
        return f"<Asset {self.symbol} ({self.exchange})>"
