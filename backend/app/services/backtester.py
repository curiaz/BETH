"""
BETHBot — Backtester service.

Orchestrates running a strategy over historical data via BacktestEngine.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd

from app.core.logging import get_logger
from app.engine.backtest_engine import BacktestEngine
from app.engine.strategy.registry import StrategyRegistry

logger = get_logger(__name__)


class BacktestService:
    """
    Service layer wrapper for BacktestEngine.
    """

    async def run(
        self,
        strategy_name: str,
        parameters: dict[str, Any],
        data: pd.DataFrame,
        symbol: str = "BTC/USDT",
        initial_capital: float = 10_000.0,
        slippage_pct: float = 0.001,
        fee_pct: float = 0.001,
        position_size_pct: float = 0.20,
        max_drawdown_pct: float = 0.15,
        max_daily_loss_pct: float = 0.03,
        max_exposure_pct: float = 0.80,
    ) -> dict[str, Any]:
        """
        Run a backtest using BacktestEngine and return formatted dictionary.
        """
        StrategyRegistry.initialize_builtin()
        strategy_cls = StrategyRegistry.get(strategy_name)
        strategy_instance = strategy_cls(**parameters)

        engine = BacktestEngine(
            initial_capital=Decimal(str(initial_capital)),
            slippage_pct=Decimal(str(slippage_pct)),
            fee_pct=Decimal(str(fee_pct)),
            position_size_pct=position_size_pct,
            max_drawdown_pct=max_drawdown_pct,
            max_daily_loss_pct=max_daily_loss_pct,
            max_exposure_pct=max_exposure_pct,
        )

        result_domain = await engine.run(
            strategy=strategy_instance,
            data=data,
            symbol=symbol,
            parameters=parameters,
        )

        return {
            "strategy_name": result_domain.strategy_name,
            "parameters": parameters,
            "symbol": result_domain.symbol,
            "timeframe": result_domain.timeframe,
            "start_date": str(result_domain.start_date),
            "end_date": str(result_domain.end_date),
            "initial_capital": float(result_domain.initial_capital),
            "final_equity": float(result_domain.final_equity),
            "total_return_pct": result_domain.total_return_pct,
            "sharpe_ratio": result_domain.sharpe_ratio,
            "sortino_ratio": result_domain.sortino_ratio,
            "max_drawdown_pct": result_domain.max_drawdown_pct,
            "win_rate": result_domain.win_rate,
            "total_trades": result_domain.total_trades,
            "profit_factor": result_domain.profit_factor,
            "avg_trade_duration_hours": result_domain.avg_trade_duration_hours,
            "equity_curve": result_domain.equity_curve,
            "trade_log": result_domain.trade_log,
        }
