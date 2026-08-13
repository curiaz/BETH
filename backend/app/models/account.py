"""
BETHBot — Account ORM model.

Represents a persistent trading account with balances.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_uuid


class AccountModel(Base, TimestampMixin):
    """Trading account ORM model."""

    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Primary Account")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USDT")

    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("10000.0")
    )
    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("10000.0")
    )
    locked_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False, default=Decimal("0.0")
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Account {self.name} ({self.currency}) balance={self.balance}>"
