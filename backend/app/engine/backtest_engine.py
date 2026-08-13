"""
BETHBot — Backtesting Engine.

Orchestrates sequential, step-by-step backtesting of trading strategies
against historical OHLCV candle data with strict prevention of look-ahead bias
and future data leakage.

Flow:
  Historical candles → Indicators → Strategy → Signal → Risk rules → Simulated execution → Portfolio → Trade records
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pandas as pd

from app.core.logging import get_logger
from app.core.market_config import market_registry
from app.domain.enums import OrderSide, OrderType, Signal
from app.domain.models import BacktestResultDomain
from app.engine.execution.backtest import BacktestExecutor
from app.engine.execution.base import OrderRequest
from app.engine.portfolio.metrics import compute_metrics
from app.engine.portfolio.tracker import PortfolioTracker
from app.engine.risk.manager import RiskManager
from app.engine.risk.rules.daily_loss import DailyLossRule
from app.engine.risk.rules.exposure import ExposureRule
from app.engine.risk.rules.max_drawdown import MaxDrawdownRule
from app.engine.risk.rules.position_size import PositionSizeRule
from app.engine.strategy.framework import SignalResult, Strategy, StrategyContext
from app.engine.strategy.registry import StrategyRegistry

logger = get_logger(__name__)


class BacktestEngine:
    """
    Quantara Backtesting Engine.

    Executes trading strategies over historical OHLCV data strictly sequentially
    to prevent look-ahead bias and future data leakage.
    """

    def __init__(
        self,
        initial_capital: Decimal = Decimal("10000.0"),
        slippage_pct: Decimal = Decimal("0.001"),
        fee_pct: Decimal = Decimal("0.001"),
        position_size_pct: float = 0.20,
        max_drawdown_pct: float = 0.15,
        max_daily_loss_pct: float = 0.03,
        max_exposure_pct: float = 0.80,
    ):
        self.initial_capital = initial_capital
        self.slippage_pct = slippage_pct
        self.fee_pct = fee_pct
        self.position_size_pct = position_size_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_exposure_pct = max_exposure_pct

    async def run(
        self,
        strategy: Strategy | str,
        data: pd.DataFrame,
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        parameters: dict[str, Any] | None = None,
    ) -> BacktestResultDomain:
        """
        Run a complete backtest sequentially.

        Args:
            strategy: Strategy instance or registered strategy name string
            data: Historical OHLCV DataFrame indexed by DatetimeIndex
            symbol: Market symbol (e.g. "BTC/USDT", "ETH/USDT")
            timeframe: Candle interval string
            parameters: Strategy parameter dictionary override

        Returns:
            BacktestResultDomain containing metrics, equity curve, and trade log
        """
        norm_symbol = market_registry.validate_symbol(symbol)

        if isinstance(strategy, str):
            strategy_cls = StrategyRegistry.get(strategy)
            strat_params = parameters or {}
            strat_instance: Strategy = strategy_cls(**strat_params)
        else:
            strat_instance = strategy

        strat_instance.reset()

        if data.empty:
            raise ValueError(f"Backtest engine received empty historical dataset for {norm_symbol}")

        logger.info(
            "backtest_engine.start",
            strategy=strat_instance.name,
            symbol=norm_symbol,
            bars=len(data),
            initial_capital=str(self.initial_capital),
        )

        # Step 1 & 2: Historical candles → Indicators calculation
        data_with_indicators = strat_instance.initialize(data)

        # Step 3: Setup components (Execution, Portfolio, Risk)
        executor = BacktestExecutor(
            slippage_pct=self.slippage_pct,
            fee_pct=self.fee_pct,
        )

        portfolio_tracker = PortfolioTracker()
        portfolio_tracker.reset(self.initial_capital)

        risk_manager = RiskManager([
            MaxDrawdownRule(self.max_drawdown_pct),
            PositionSizeRule(self.position_size_pct),
            DailyLossRule(self.max_daily_loss_pct),
            ExposureRule(self.max_exposure_pct),
        ])

        trade_log: list[dict[str, Any]] = []
        current_day: datetime | None = None

        # Step 4: Sequential Bar-by-Bar Loop (Prevents look-ahead bias & future data leakage)
        for idx in range(len(data_with_indicators)):
            bar = data_with_indicators.iloc[idx]
            bar_time = data_with_indicators.index[idx]

            if isinstance(bar_time, pd.Timestamp):
                bar_dt = bar_time.to_pydatetime()
            elif isinstance(bar_time, datetime):
                bar_dt = bar_time
            else:
                bar_dt = datetime.now(timezone.utc)

            # Day boundary tracking for daily loss rule
            if current_day is None or (hasattr(bar_dt, "date") and bar_dt.date() != current_day):
                portfolio_tracker.start_new_day()
                current_day = bar_dt.date() if hasattr(bar_dt, "date") else current_day

            # Update current market price
            current_price = Decimal(str(bar["close"]))
            portfolio_tracker.update_price(norm_symbol, current_price)
            executor.set_current_bar(bar)

            # Get current portfolio state for strategy context
            portfolio_state = portfolio_tracker.get_portfolio_state()

            # Extract indicator dictionary for current bar only
            indicators = {
                k: v
                for k, v in bar.to_dict().items()
                if k not in ("open", "high", "low", "close", "volume")
            }

            # Construct StrategyContext for ONLY the current bar
            context = StrategyContext(
                symbol=norm_symbol,
                timeframe=timeframe,
                candle=bar,
                indicators=indicators,
                timestamp=bar_dt,
                portfolio_state=portfolio_state,
            )

            # Step 5: Strategy → Signal
            signal_result: SignalResult = strat_instance.generate_signal(context)

            # Step 6: Signal → Risk rules → Simulated execution
            if signal_result.is_actionable:
                side = OrderSide.BUY if signal_result.direction == Signal.BUY else OrderSide.SELL

                # Skip SELL if no open position exists
                if side == OrderSide.SELL and norm_symbol not in portfolio_tracker.positions:
                    portfolio_tracker.record_equity(bar_dt)
                    continue

                # Calculate quantity based on position sizing and signal strength
                if side == OrderSide.BUY:
                    available_cash = float(portfolio_tracker.cash)
                    allocated_cash = available_cash * self.position_size_pct * signal_result.strength
                    if current_price > 0:
                        quantity = Decimal(str(allocated_cash)) / current_price
                    else:
                        quantity = Decimal("0")
                else:
                    # Sell entire position
                    quantity = portfolio_tracker.positions.get(norm_symbol, Decimal("0"))

                if quantity > 0:
                    order = OrderRequest(
                        asset_symbol=norm_symbol,
                        side=side,
                        order_type=OrderType.MARKET,
                        quantity=quantity,
                    )

                    # Risk evaluation
                    evaluations = risk_manager.evaluate(order, portfolio_state, current_price)

                    if risk_manager.is_approved(evaluations):
                        # Simulated execution
                        fill = await executor.submit_order(order)

                        # Step 7: Portfolio update
                        portfolio_tracker.process_fill(fill)

                        # Step 8: Trade records
                        trade_entry = {
                            "timestamp": bar_dt.isoformat(),
                            "symbol": norm_symbol,
                            "side": fill.side.value,
                            "quantity": float(fill.quantity),
                            "price": float(fill.price),
                            "fee": float(fill.fee),
                            "slippage": float(fill.slippage),
                            "realized_pnl": float(portfolio_tracker.realized_pnl)
                            if side == OrderSide.SELL
                            else 0.0,
                        }
                        trade_log.append(trade_entry)

                        strat_instance.on_trade(trade_entry)

            # Record portfolio equity curve at step idx
            portfolio_tracker.record_equity(bar_dt)

        # Step 9: Compute performance metrics
        metrics = compute_metrics(
            equity_curve=portfolio_tracker.equity_history,
            trades=trade_log,
            initial_capital=float(self.initial_capital),
        )

        start_date = data.index[0] if len(data) > 0 else datetime.now(timezone.utc)
        end_date = data.index[-1] if len(data) > 0 else datetime.now(timezone.utc)

        start_dt = start_date.to_pydatetime() if hasattr(start_date, "to_pydatetime") else start_date
        end_dt = end_date.to_pydatetime() if hasattr(end_date, "to_pydatetime") else end_date

        result = BacktestResultDomain(
            strategy_name=strat_instance.name,
            symbol=norm_symbol,
            timeframe=timeframe,
            start_date=start_dt,
            end_date=end_dt,
            initial_capital=self.initial_capital,
            final_equity=Decimal(str(metrics.final_equity)),
            total_return_pct=metrics.total_return_pct,
            sharpe_ratio=metrics.sharpe_ratio,
            sortino_ratio=metrics.sortino_ratio,
            max_drawdown_pct=metrics.max_drawdown_pct,
            win_rate=metrics.win_rate,
            total_trades=metrics.total_trades,
            profit_factor=metrics.profit_factor,
            avg_trade_duration_hours=metrics.avg_trade_duration_hours,
            equity_curve=[
                {"timestamp": ts.isoformat(), "equity": eq}
                for ts, eq in portfolio_tracker.equity_history
            ],
            trade_log=trade_log,
        )

        logger.info(
            "backtest_engine.complete",
            strategy=strat_instance.name,
            symbol=norm_symbol,
            return_pct=metrics.total_return_pct,
            total_trades=metrics.total_trades,
            final_equity=str(result.final_equity),
        )

        return result
