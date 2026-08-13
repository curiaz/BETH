"""
BETHBot — Backtest result ORM model.

Stores backtest configuration, performance metrics, equity curve, and trade log.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BacktestResult(Base):
    """Stores the complete results of a backtest run."""

    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Configuration
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(5), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Capital
    initial_capital: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )
    final_equity: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=8), nullable=False
    )

    # Performance metrics
    total_return_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    sortino_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    profit_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_trade_duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Detailed data (JSON strings)
    equity_curve_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    trade_log_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    asset = relationship("Asset")

    __table_args__ = (
        Index("idx_backtest_strategy", "strategy_name", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<BacktestResult {self.strategy_name} "
            f"return={self.total_return_pct:.1f}% trades={self.total_trades}>"
        )
