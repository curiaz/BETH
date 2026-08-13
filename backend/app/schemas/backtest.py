"""
BETHBot — Pydantic schemas: Backtest.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    """Backtest launch request."""

    strategy_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10_000.0
    slippage_pct: float = 0.001
    fee_pct: float = 0.001


class BacktestResultResponse(BaseModel):
    """Backtest result response."""

    id: int
    strategy_name: str
    parameters: dict[str, Any] | None = None
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_equity: float
    total_return_pct: float
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    profit_factor: float | None = None
    avg_trade_duration_hours: float | None = None
    equity_curve: list[dict] | None = None
    trade_log: list[dict] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
