"""
BETHBot — Strategy state ORM model.

Persists strategy configuration and internal state so strategies survive restarts.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class StrategyState(Base, TimestampMixin):
    """Persisted strategy configuration and internal state."""

    __tablename__ = "strategy_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")

    # Strategy parameters (JSON string)
    parameters_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Internal state (JSON string) — for strategy restart recovery
    state_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    signals = relationship("Signal", back_populates="strategy_state", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<StrategyState {self.strategy_name} v{self.version} active={self.is_active}>"
