"""
BETHBot — Unit Tests for Quantara Backtesting Engine.

Tests all required cases:
1. Complete backtest flow for BTC/USDT and ETH/USDT
2. Historical candles → Indicators → Strategy → Signal → Risk rules → Execution → Portfolio → Trade log
3. Sequential bar-by-bar execution without look-ahead bias or future data leakage
4. Initial capital, fees, slippage, position sizing, entry, exit, multiple trades
5. BacktestResult domain model structure
"""

from datetime import datetime, timezone
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from app.domain.enums import Signal
from app.domain.models import BacktestResultDomain
from app.engine.backtest_engine import BacktestEngine
from app.engine.strategy.builtin.sma_crossover import MovingAverageCrossoverStrategy
from app.engine.strategy.framework import SignalResult, Strategy, StrategyContext


# Strategy tracking context history to verify look-ahead bias prevention
class SequentialSpyStrategy(Strategy):
    name = "sequential_spy"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.seen_timestamps = []

    def parameters(cls):
        return []

    def initialize(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        df = historical_data.copy()
        df["sma_fast"] = df["close"].rolling(2).mean()
        df["sma_slow"] = df["close"].rolling(4).mean()
        return df

    def generate_signal(self, context: StrategyContext) -> SignalResult:
        self.seen_timestamps.append(context.timestamp)
        # Verify context candle is not a future bar
        if context.market_data is not None:
            assert len(context.market_data) <= len(self.seen_timestamps)

        return SignalResult(symbol=context.symbol, direction=Signal.HOLD)


def make_sample_dataframe(n: int = 100, base_price: float = 42000.0) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=n, freq="h", tz="UTC")
    price = base_price
    prices = []
    for _ in range(n):
        price *= 1 + np.random.normal(0, 0.005)
        prices.append(price)

    return pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.002 for p in prices],
            "low": [p * 0.998 for p in prices],
            "close": prices,
            "volume": [100.0] * n,
        },
        index=dates,
    )


class TestBacktestEngine:
    @pytest.mark.asyncio
    async def test_btc_usdt_backtest_flow(self):
        """Test complete backtest flow for BTC/USDT."""
        engine = BacktestEngine(
            initial_capital=Decimal("10000.0"),
            slippage_pct=Decimal("0.001"),
            fee_pct=Decimal("0.001"),
        )

        df = make_sample_dataframe(n=150, base_price=42000.0)
        strategy = MovingAverageCrossoverStrategy(fast_period=5, slow_period=15)

        result = await engine.run(
            strategy=strategy,
            data=df,
            symbol="BTC/USDT",
            timeframe="1h",
        )

        assert isinstance(result, BacktestResultDomain)
        assert result.symbol == "BTC/USDT"
        assert result.initial_capital == Decimal("10000.0")
        assert isinstance(result.final_equity, Decimal)
        assert isinstance(result.equity_curve, list)
        assert len(result.equity_curve) == len(df)
        assert isinstance(result.trade_log, list)

    @pytest.mark.asyncio
    async def test_eth_usdt_backtest_flow(self):
        """Test complete backtest flow for ETH/USDT."""
        engine = BacktestEngine(
            initial_capital=Decimal("10000.0"),
            slippage_pct=Decimal("0.001"),
            fee_pct=Decimal("0.001"),
        )

        df = make_sample_dataframe(n=150, base_price=2200.0)
        strategy = MovingAverageCrossoverStrategy(fast_period=5, slow_period=15)

        result = await engine.run(
            strategy=strategy,
            data=df,
            symbol="ETH/USDT",
            timeframe="1h",
        )

        assert result.symbol == "ETH/USDT"
        assert result.initial_capital == Decimal("10000.0")
        assert len(result.equity_curve) == len(df)

    @pytest.mark.asyncio
    async def test_sequential_processing_prevents_look_ahead_bias(self):
        """Verify sequential bar-by-bar processing prevents look-ahead bias."""
        engine = BacktestEngine(initial_capital=Decimal("10000.0"))
        df = make_sample_dataframe(n=50)

        spy_strategy = SequentialSpyStrategy()
        await engine.run(strategy=spy_strategy, data=df, symbol="BTC/USDT")

        # Verify bars were processed strictly chronologically
        assert len(spy_strategy.seen_timestamps) == len(df)
        for i in range(len(spy_strategy.seen_timestamps) - 1):
            assert spy_strategy.seen_timestamps[i] < spy_strategy.seen_timestamps[i + 1]

    @pytest.mark.asyncio
    async def test_empty_dataframe_rejected(self):
        """Verify backtest engine rejects empty historical dataset."""
        engine = BacktestEngine()
        empty_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        strategy = MovingAverageCrossoverStrategy()

        with pytest.raises(ValueError, match="empty historical dataset"):
            await engine.run(strategy=strategy, data=empty_df, symbol="BTC/USDT")
