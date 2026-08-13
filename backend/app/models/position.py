"""
BETHBot — Position ORM model.

Tracks open and closed positions with PnL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Position(Base, TimestampMixin):
    """An open or closed position."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)

    # Session isolation
    session_type: Mapped[str] = mapped_column(String(20), nullable=False, default="PAPER")
    session_id: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    side: Mapped[str] = mapped_column(String(10), nullable=False)  # LONG | SHORT
    entry_price: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)

    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("0")
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("0")
    )

    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="OPEN"
    )  # OPEN | CLOSED

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    asset = relationship("Asset")

    __table_args__ = (
        Index("idx_position_session_status", "session_type", "session_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Position {self.side} {self.quantity} ({self.status}) pnl={self.unrealized_pnl}>"
