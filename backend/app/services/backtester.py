"""
BETHBot — Backtester service.

Orchestrates running a strategy over historical data with simulated fills.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd

from app.core.logging import get_logger
from app.engine.execution.backtest import BacktestExecutor
from app.engine.execution.base import OrderRequest, OrderSide, OrderType
from app.engine.portfolio.metrics import PerformanceMetrics, compute_metrics
from app.engine.portfolio.tracker import PortfolioTracker
from app.engine.risk.manager import RiskManager
from app.engine.risk.rules.daily_loss import DailyLossRule
from app.engine.risk.rules.exposure import ExposureRule
from app.engine.risk.rules.max_drawdown import MaxDrawdownRule
from app.engine.risk.rules.position_size import PositionSizeRule
from app.engine.strategy.base import BaseStrategy, SignalDirection
from app.engine.strategy.registry import StrategyRegistry

logger = get_logger(__name__)


class BacktestService:
    """
    Runs a trading strategy over historical OHLCV data and produces
    performance metrics, equity curves, and trade logs.
    """

    async def run(
        self,
        strategy_name: str,
        parameters: dict,
        data: pd.DataFrame,
        symbol: str = "BTC/USDT",
        initial_capital: float = 10_000.0,
        slippage_pct: float = 0.001,
        fee_pct: float = 0.001,
        position_size_pct: float = 0.20,
        max_drawdown_pct: float = 0.15,
        max_daily_loss_pct: float = 0.03,
        max_exposure_pct: float = 0.80,
    ) -> dict:
        """
        Run a complete backtest.

        Args:
            strategy_name: Registered strategy name
            parameters: Strategy constructor parameters
            data: DataFrame with OHLCV columns and DatetimeIndex
            symbol: Trading pair symbol
            initial_capital: Starting capital in USDT
            slippage_pct: Slippage percentage per trade
            fee_pct: Fee percentage per trade
            position_size_pct: Max position size as % of equity
            max_drawdown_pct: Max drawdown before halting
            max_daily_loss_pct: Max daily loss before halting
            max_exposure_pct: Max total exposure

        Returns:
            Dict with metrics, equity curve, and trade log
        """
        logger.info(
            "backtest.start",
            strategy=strategy_name,
            symbol=symbol,
            bars=len(data),
            capital=initial_capital,
        )

        # Get strategy class and instantiate
        strategy_cls = StrategyRegistry.get(strategy_name)
        strategy: BaseStrategy = strategy_cls(**parameters)
        strategy.reset()

        # Initialize indicators on full history
        data = strategy.initialize(data)

        # Set up execution
        executor = BacktestExecutor(
            slippage_pct=Decimal(str(slippage_pct)),
            fee_pct=Decimal(str(fee_pct)),
        )

        # Set up portfolio tracker
        tracker = PortfolioTracker()
        tracker.reset(Decimal(str(initial_capital)))

        # Set up risk manager
        risk_manager = RiskManager([
            MaxDrawdownRule(max_drawdown_pct),
            PositionSizeRule(position_size_pct),
            DailyLossRule(max_daily_loss_pct),
            ExposureRule(max_exposure_pct),
        ])

        # Trade log
        trades: list[dict] = []
        current_day: datetime | None = None

        # --- Bar-by-bar processing ---
        for idx in range(len(data)):
            bar = data.iloc[idx]
            bar_time = data.index[idx]

            # Convert to datetime if needed
            if isinstance(bar_time, pd.Timestamp):
                bar_dt = bar_time.to_pydatetime()
            else:
                bar_dt = bar_time

            # Track daily boundaries
            if current_day is None or (hasattr(bar_dt, 'date') and bar_dt.date() != current_day):
                tracker.start_new_day()
                current_day = bar_dt.date() if hasattr(bar_dt, 'date') else current_day

            # Update current price
            current_price = Decimal(str(bar["close"]))
            tracker.update_price(symbol, current_price)

            # Set current bar for executor
            executor.set_current_bar(bar)

            # Get portfolio state
            portfolio_state = tracker.get_portfolio_state()

            # Generate signal
            signal = strategy.on_bar(bar, portfolio_state)

            if signal.is_actionable:
                # Determine order details
                side = OrderSide.BUY if signal.direction == SignalDirection.BUY else OrderSide.SELL

                # Skip SELL if no position
                if side == OrderSide.SELL and symbol not in tracker.positions:
                    tracker.record_equity(bar_dt)
                    continue

                # Calculate quantity
                if side == OrderSide.BUY:
                    # Size based on signal strength and available capital
                    available = float(tracker.cash) * position_size_pct * signal.strength
                    if current_price > 0:
                        quantity = Decimal(str(available)) / current_price
                    else:
                        quantity = Decimal("0")
                else:
                    # Sell entire position
                    quantity = tracker.positions.get(symbol, Decimal("0"))

                if quantity > 0:
                    order = OrderRequest(
                        asset_symbol=symbol,
                        side=side,
                        order_type=OrderType.MARKET,
                        quantity=quantity,
                    )

                    # Risk check
                    evaluations = risk_manager.evaluate(
                        order, portfolio_state, current_price
                    )

                    if risk_manager.is_approved(evaluations):
                        fill = await executor.submit_order(order)
                        tracker.process_fill(fill)

                        # Log trade
                        trades.append({
                            "timestamp": bar_dt.isoformat() if hasattr(bar_dt, 'isoformat') else str(bar_dt),
                            "side": fill.side.value,
                            "quantity": float(fill.quantity),
                            "price": float(fill.price),
                            "fee": float(fill.fee),
                            "pnl": float(tracker.realized_pnl) if side == OrderSide.SELL else 0,
                        })

                        strategy.on_trade({
                            "side": fill.side.value,
                            "price": float(fill.price),
                            "quantity": float(fill.quantity),
                        })

            # Record equity
            tracker.record_equity(bar_dt)

        # --- Compute metrics ---
        metrics = compute_metrics(
            equity_curve=tracker.equity_history,
            trades=trades,
            initial_capital=initial_capital,
        )

        # Build result
        start_date = data.index[0] if len(data) > 0 else datetime.now(timezone.utc)
        end_date = data.index[-1] if len(data) > 0 else datetime.now(timezone.utc)

        result = {
            "strategy_name": strategy_name,
            "parameters": parameters,
            "symbol": symbol,
            "timeframe": "1h",
            "start_date": str(start_date),
            "end_date": str(end_date),
            "initial_capital": initial_capital,
            "final_equity": metrics.final_equity,
            "total_return_pct": metrics.total_return_pct,
            "sharpe_ratio": metrics.sharpe_ratio,
            "sortino_ratio": metrics.sortino_ratio,
            "max_drawdown_pct": metrics.max_drawdown_pct,
            "win_rate": metrics.win_rate,
            "total_trades": metrics.total_trades,
            "profit_factor": metrics.profit_factor,
            "avg_trade_duration_hours": metrics.avg_trade_duration_hours,
            "equity_curve": [
                {"timestamp": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts), "equity": eq}
                for ts, eq in tracker.equity_history
            ],
            "trade_log": trades,
        }

        logger.info(
            "backtest.complete",
            strategy=strategy_name,
            return_pct=metrics.total_return_pct,
            trades=metrics.total_trades,
            sharpe=metrics.sharpe_ratio,
        )

        return result
