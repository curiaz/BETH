"""
BETHBot — Trade (Fill) ORM model.

Represents a realized fill from an order execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Trade(Base):
    """A realized trade / fill. Links back to the originating order."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)

    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY | SELL
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    fee: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("0")
    )
    slippage: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("0")
    )

    # Session isolation
    session_type: Mapped[str] = mapped_column(String(20), nullable=False, default="PAPER")
    session_id: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    order = relationship("Order", back_populates="trades")
    asset = relationship("Asset")

    __table_args__ = (
        Index("idx_trade_session", "session_type", "session_id", "executed_at"),
    )

    def __repr__(self) -> str:
        return f"<Trade {self.side} {self.quantity}@{self.price} fee={self.fee}>"
