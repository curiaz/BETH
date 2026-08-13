"""
BETHBot — Order ORM model.

Represents an order intent. Session-type isolation (BACKTEST/PAPER/LIVE)
keeps data from different modes separated in the same table.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    """An order intent — may result in zero or more trades/fills."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    signal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("signals.id"), nullable=True
    )

    # Session isolation
    session_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PAPER"
    )  # BACKTEST | PAPER | LIVE
    session_id: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )

    # Order details
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY | SELL
    order_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MARKET"
    )  # MARKET | LIMIT | STOP | STOP_LIMIT
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=20, scale=8), nullable=True
    )  # Required for LIMIT
    stop_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=20, scale=8), nullable=True
    )  # Required for STOP

    # Status lifecycle
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )  # PENDING → SUBMITTED → FILLED / CANCELLED / REJECTED
    reject_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    filled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    asset = relationship("Asset")
    signal = relationship("Signal")
    trades = relationship("Trade", back_populates="order", lazy="selectin")

    __table_args__ = (
        Index("idx_order_session", "session_type", "session_id", "created_at"),
        Index("idx_order_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Order {self.side} {self.order_type} {self.quantity} ({self.status})>"
