"""
BETHBot — Portfolio performance metrics.

Computes Sharpe, Sortino, max drawdown, win rate, and other
performance metrics from equity history and trade data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass
class PerformanceMetrics:
    """Complete performance metrics for a trading session."""

    total_return_pct: float = 0.0
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    profit_factor: float | None = None
    avg_trade_duration_hours: float | None = None
    initial_capital: float = 0.0
    final_equity: float = 0.0


def compute_metrics(
    equity_curve: list[tuple[datetime, float]],
    trades: list[dict],
    initial_capital: float,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252 * 24,  # hourly bars, ~252 trading days
) -> PerformanceMetrics:
    """
    Compute comprehensive performance metrics.

    Args:
        equity_curve: List of (timestamp, equity) tuples
        trades: List of trade dicts with 'pnl' and optional 'duration_hours' keys
        initial_capital: Starting capital
        risk_free_rate: Annual risk-free rate (default 0)
        periods_per_year: Number of data periods per year (for annualization)

    Returns:
        PerformanceMetrics dataclass
    """
    if not equity_curve:
        return PerformanceMetrics(initial_capital=initial_capital, final_equity=initial_capital)

    equities = np.array([e[1] for e in equity_curve], dtype=np.float64)
    final_equity = float(equities[-1])
    total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100

    # --- Returns ---
    returns = np.diff(equities) / equities[:-1] if len(equities) > 1 else np.array([])

    # --- Sharpe Ratio ---
    sharpe = None
    if len(returns) > 1:
        mean_return = float(np.mean(returns))
        std_return = float(np.std(returns, ddof=1))
        if std_return > 0:
            excess_return = mean_return - (risk_free_rate / periods_per_year)
            sharpe = round(excess_return / std_return * math.sqrt(periods_per_year), 4)

    # --- Sortino Ratio ---
    sortino = None
    if len(returns) > 1:
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_std = float(np.std(downside_returns, ddof=1))
            if downside_std > 0:
                mean_return = float(np.mean(returns))
                excess_return = mean_return - (risk_free_rate / periods_per_year)
                sortino = round(excess_return / downside_std * math.sqrt(periods_per_year), 4)

    # --- Max Drawdown ---
    max_drawdown_pct = 0.0
    if len(equities) > 1:
        cumulative_max = np.maximum.accumulate(equities)
        drawdowns = (cumulative_max - equities) / cumulative_max
        max_drawdown_pct = round(float(np.max(drawdowns)) * 100, 4)

    # --- Trade Statistics ---
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
    losing_trades = sum(1 for t in trades if t.get("pnl", 0) < 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

    # --- Profit Factor ---
    profit_factor = None
    if trades:
        gross_profit = sum(t["pnl"] for t in trades if t.get("pnl", 0) > 0)
        gross_loss = abs(sum(t["pnl"] for t in trades if t.get("pnl", 0) < 0))
        if gross_loss > 0:
            profit_factor = round(gross_profit / gross_loss, 4)

    # --- Avg Trade Duration ---
    avg_duration = None
    durations = [t["duration_hours"] for t in trades if "duration_hours" in t]
    if durations:
        avg_duration = round(sum(durations) / len(durations), 2)

    return PerformanceMetrics(
        total_return_pct=round(total_return_pct, 4),
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        max_drawdown_pct=max_drawdown_pct,
        win_rate=round(win_rate, 2),
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        profit_factor=profit_factor,
        avg_trade_duration_hours=avg_duration,
        initial_capital=initial_capital,
        final_equity=final_equity,
    )
