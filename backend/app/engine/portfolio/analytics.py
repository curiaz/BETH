"""
BETHBot — Performance Analytics & Reporting.

Calculates comprehensive backtest performance analytics, strategy vs. market performance,
trade metrics, independent asset reports for BTC/USDT and ETH/USDT, and comparative asset reports.

Includes explicit disclaimers: Historical simulations do NOT guarantee live trading profitability.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.domain.models import BacktestResultDomain


class BacktestReport(BaseModel):
    """
    Detailed Backtest Performance Report.
    """

    symbol: str = Field(description="Market symbol, e.g. BTC/USDT or ETH/USDT")
    strategy_name: str
    timeframe: str = "1h"
    start_date: datetime
    end_date: datetime

    # Balance & Returns
    starting_balance: Decimal
    ending_balance: Decimal
    net_pnl: Decimal
    total_return_pct: float

    # Strategy vs. Market Performance Distinction
    market_return_pct: float | None = Field(
        default=None, description="Buy & Hold return of the underlying asset over the same period"
    )
    strategy_alpha_pct: float | None = Field(
        default=None, description="Excess return of strategy over market Buy & Hold"
    )

    # Trade Statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate_pct: float = 0.0

    avg_trade_pnl: float = 0.0
    avg_winning_trade_pnl: float = 0.0
    avg_losing_trade_pnl: float = 0.0

    profit_factor: float | None = None
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float | None = Field(
        default=None, description="Annualized Sharpe ratio (calculated when statistically appropriate)"
    )

    equity_curve: list[dict[str, Any]] = Field(default_factory=list)
    trade_log: list[dict[str, Any]] = Field(default_factory=list)

    disclaimer: str = Field(
        default=(
            "DISCLAIMER: Backtest performance metrics are historical simulations based on "
            "past market data. Past performance and simulated backtest results do NOT guarantee "
            "or imply profitability in live trading environments."
        )
    )


class AssetComparisonReport(BaseModel):
    """
    Comparative report analyzing backtest performance across multiple assets (e.g., BTC/USDT vs. ETH/USDT).
    """

    strategy_name: str
    timeframe: str
    reports: dict[str, BacktestReport] = Field(description="Map of symbol -> BacktestReport")

    summary_table: list[dict[str, Any]] = Field(default_factory=list)

    best_returning_asset: str | None = None
    lowest_drawdown_asset: str | None = None
    highest_sharpe_asset: str | None = None

    disclaimer: str = Field(
        default=(
            "DISCLAIMER: Comparative backtest analytics are provided for research purposes only. "
            "Simulated historical advantages do NOT guarantee future live trading profits."
        )
    )


class PerformanceAnalytics:
    """
    Analytics engine for calculating trade metrics, market benchmarks, and generating reports.
    """

    @staticmethod
    def calculate_analytics(
        starting_balance: float | Decimal,
        equity_curve: list[tuple[datetime, float] | dict[str, Any]],
        trades: list[dict[str, Any]],
        market_candles: pd.DataFrame | None = None,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252 * 24,
    ) -> dict[str, Any]:
        """
        Calculate all performance metrics.
        """
        start_bal = float(starting_balance)

        # Extract equity curve array
        if not equity_curve:
            end_bal = start_bal
            equities = np.array([start_bal])
        elif isinstance(equity_curve[0], dict):
            equities = np.array([float(e["equity"]) for e in equity_curve], dtype=np.float64)
            end_bal = float(equities[-1])
        else:
            equities = np.array([float(e[1]) for e in equity_curve], dtype=np.float64)
            end_bal = float(equities[-1])

        net_pnl = end_bal - start_bal
        total_return_pct = ((end_bal - start_bal) / start_bal * 100.0) if start_bal > 0 else 0.0

        # Market performance (Buy & Hold return) calculation
        market_return_pct = None
        strategy_alpha_pct = None
        if market_candles is not None and not market_candles.empty and "close" in market_candles.columns:
            open_start = float(market_candles["close"].iloc[0])
            close_end = float(market_candles["close"].iloc[-1])
            if open_start > 0:
                market_return_pct = round(((close_end - open_start) / open_start) * 100.0, 4)
                strategy_alpha_pct = round(total_return_pct - market_return_pct, 4)

        # Returns & Sharpe ratio (statistically appropriate: n >= 2, std > 0)
        returns = np.diff(equities) / equities[:-1] if len(equities) > 1 else np.array([])
        sharpe = None
        if len(returns) > 1:
            std_ret = float(np.std(returns, ddof=1))
            mean_ret = float(np.mean(returns))
            if std_ret > 0:
                excess = mean_ret - (risk_free_rate / periods_per_year)
                sharpe = round((excess / std_ret) * math.sqrt(periods_per_year), 4)

        # Max Drawdown
        max_drawdown_pct = 0.0
        if len(equities) > 1:
            cum_max = np.maximum.accumulate(equities)
            drawdowns = (cum_max - equities) / cum_max
            max_drawdown_pct = round(float(np.max(drawdowns)) * 100.0, 4)

        # Trade metrics
        total_trades = len(trades)
        wins = [t.get("realized_pnl", t.get("pnl", 0.0)) for t in trades if t.get("realized_pnl", t.get("pnl", 0.0)) > 0]
        losses = [t.get("realized_pnl", t.get("pnl", 0.0)) for t in trades if t.get("realized_pnl", t.get("pnl", 0.0)) < 0]

        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate_pct = round((winning_trades / total_trades * 100.0), 2) if total_trades > 0 else 0.0

        all_pnls = [t.get("realized_pnl", t.get("pnl", 0.0)) for t in trades]
        avg_trade_pnl = round(sum(all_pnls) / total_trades, 4) if total_trades > 0 else 0.0
        avg_win_pnl = round(sum(wins) / winning_trades, 4) if winning_trades > 0 else 0.0
        avg_loss_pnl = round(sum(losses) / losing_trades, 4) if losing_trades > 0 else 0.0

        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = round(gross_profit / gross_loss, 4) if gross_loss > 0 else None

        return {
            "starting_balance": Decimal(str(start_bal)),
            "ending_balance": Decimal(str(end_bal)),
            "net_pnl": Decimal(str(net_pnl)),
            "total_return_pct": round(total_return_pct, 4),
            "market_return_pct": market_return_pct,
            "strategy_alpha_pct": strategy_alpha_pct,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate_pct": win_rate_pct,
            "avg_trade_pnl": avg_trade_pnl,
            "avg_winning_trade_pnl": avg_win_pnl,
            "avg_losing_trade_pnl": avg_loss_pnl,
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_drawdown_pct,
            "sharpe_ratio": sharpe,
        }

    @classmethod
    def generate_report(
        cls,
        backtest_result: BacktestResultDomain | dict[str, Any],
        market_candles: pd.DataFrame | None = None,
    ) -> BacktestReport:
        """
        Generate a detailed BacktestReport for a single asset (BTC/USDT or ETH/USDT).
        """
        if isinstance(backtest_result, BacktestResultDomain):
            res_dict = backtest_result.model_dump()
        else:
            res_dict = backtest_result

        symbol = res_dict.get("symbol", "BTC/USDT")
        strategy_name = res_dict.get("strategy_name", "sma_crossover")
        timeframe = res_dict.get("timeframe", "1h")
        start_date = res_dict.get("start_date", datetime.now(timezone.utc))
        end_date = res_dict.get("end_date", datetime.now(timezone.utc))
        init_capital = res_dict.get("initial_capital", 10000.0)

        equity_curve = res_dict.get("equity_curve", [])
        trade_log = res_dict.get("trade_log", [])

        analytics = cls.calculate_analytics(
            starting_balance=init_capital,
            equity_curve=equity_curve,
            trades=trade_log,
            market_candles=market_candles,
        )

        return BacktestReport(
            symbol=symbol,
            strategy_name=strategy_name,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            starting_balance=analytics["starting_balance"],
            ending_balance=analytics["ending_balance"],
            net_pnl=analytics["net_pnl"],
            total_return_pct=analytics["total_return_pct"],
            market_return_pct=analytics["market_return_pct"],
            strategy_alpha_pct=analytics["strategy_alpha_pct"],
            total_trades=analytics["total_trades"],
            winning_trades=analytics["winning_trades"],
            losing_trades=analytics["losing_trades"],
            win_rate_pct=analytics["win_rate_pct"],
            avg_trade_pnl=analytics["avg_trade_pnl"],
            avg_winning_trade_pnl=analytics["avg_winning_trade_pnl"],
            avg_losing_trade_pnl=analytics["avg_losing_trade_pnl"],
            profit_factor=analytics["profit_factor"],
            max_drawdown_pct=analytics["max_drawdown_pct"],
            sharpe_ratio=analytics["sharpe_ratio"],
            equity_curve=equity_curve,
            trade_log=trade_log,
        )

    @classmethod
    def generate_comparison_report(
        cls,
        reports: list[BacktestReport] | dict[str, BacktestReport],
    ) -> AssetComparisonReport:
        """
        Generate a comparative analytics report between multiple assets (e.g. BTC/USDT vs. ETH/USDT).
        """
        if isinstance(reports, list):
            report_map = {r.symbol: r for r in reports}
        else:
            report_map = reports

        if not report_map:
            raise ValueError("At least one BacktestReport is required for comparison.")

        first_report = next(iter(report_map.values()))
        strategy_name = first_report.strategy_name
        timeframe = first_report.timeframe

        summary_table = []
        best_ret_symbol = None
        best_ret = -float("inf")
        lowest_dd_symbol = None
        lowest_dd = float("inf")
        highest_sharpe_symbol = None
        highest_sharpe = -float("inf")

        for symbol, rep in report_map.items():
            summary_table.append({
                "symbol": symbol,
                "total_return_pct": rep.total_return_pct,
                "market_return_pct": rep.market_return_pct,
                "strategy_alpha_pct": rep.strategy_alpha_pct,
                "win_rate_pct": rep.win_rate_pct,
                "total_trades": rep.total_trades,
                "max_drawdown_pct": rep.max_drawdown_pct,
                "profit_factor": rep.profit_factor,
                "sharpe_ratio": rep.sharpe_ratio,
            })

            if rep.total_return_pct > best_ret:
                best_ret = rep.total_return_pct
                best_ret_symbol = symbol

            if rep.max_drawdown_pct < lowest_dd:
                lowest_dd = rep.max_drawdown_pct
                lowest_dd_symbol = symbol

            if rep.sharpe_ratio is not None and rep.sharpe_ratio > highest_sharpe:
                highest_sharpe = rep.sharpe_ratio
                highest_sharpe_symbol = symbol

        return AssetComparisonReport(
            strategy_name=strategy_name,
            timeframe=timeframe,
            reports=report_map,
            summary_table=summary_table,
            best_returning_asset=best_ret_symbol,
            lowest_drawdown_asset=lowest_dd_symbol,
            highest_sharpe_asset=highest_sharpe_symbol,
        )
