"""
BETHBot — Portfolio snapshot ORM model.

Point-in-time portfolio state for equity curve charting and performance analysis.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PortfolioSnapshot(Base):
    """Point-in-time portfolio state."""

    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Session isolation
    session_type: Mapped[str] = mapped_column(String(20), nullable=False, default="PAPER")
    session_id: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    total_equity: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )
    cash_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )
    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("0")
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("0")
    )

    # Per-asset breakdown as JSON string
    allocations_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_portfolio_session_time", "session_type", "session_id", "snapshot_at"),
    )

    def __repr__(self) -> str:
        return f"<PortfolioSnapshot equity={self.total_equity} at {self.snapshot_at}>"
