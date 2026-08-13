"""
BETHBot — Integration tests: Backtester.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from app.services.backtester import BacktestService
from app.engine.strategy.registry import StrategyRegistry


@pytest.fixture(autouse=True)
def init_strategies():
    """Ensure strategies are registered before each test."""
    StrategyRegistry.initialize_builtin()


@pytest.fixture
def ohlcv_data():
    """Generate 500 bars of sample data."""
    np.random.seed(42)
    dates = pd.date_range(
        start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        periods=500,
        freq="h",
    )
    price = 42000.0
    prices = []
    for _ in range(500):
        price *= 1 + np.random.normal(0, 0.005)
        prices.append(price)

    return pd.DataFrame(
        {
            "open": prices,
            "high": [p * (1 + abs(np.random.normal(0, 0.003))) for p in prices],
            "low": [p * (1 - abs(np.random.normal(0, 0.003))) for p in prices],
            "close": [p * (1 + np.random.normal(0, 0.001)) for p in prices],
            "volume": [abs(np.random.normal(100, 30)) for _ in prices],
        },
        index=dates,
    )


@pytest.mark.asyncio
async def test_backtest_sma_crossover(ohlcv_data):
    """Run a complete SMA Crossover backtest and verify result structure."""
    service = BacktestService()
    result = await service.run(
        strategy_name="sma_crossover",
        parameters={"fast_period": 10, "slow_period": 30},
        data=ohlcv_data,
        symbol="BTC/USDT",
        initial_capital=10000,
    )

    assert "strategy_name" in result
    assert result["strategy_name"] == "sma_crossover"
    assert "total_return_pct" in result
    assert "sharpe_ratio" in result
    assert "max_drawdown_pct" in result
    assert "equity_curve" in result
    assert "trade_log" in result
    assert isinstance(result["equity_curve"], list)
    assert len(result["equity_curve"]) > 0
    assert result["initial_capital"] == 10000


@pytest.mark.asyncio
async def test_backtest_rsi_mean_reversion(ohlcv_data):
    """Run a complete RSI Mean Reversion backtest."""
    service = BacktestService()
    result = await service.run(
        strategy_name="rsi_mean_reversion",
        parameters={"rsi_period": 14, "oversold": 30.0, "overbought": 70.0},
        data=ohlcv_data,
        symbol="ETH/USDT",
        initial_capital=10000,
    )

    assert result["strategy_name"] == "rsi_mean_reversion"
    assert "total_return_pct" in result
    assert isinstance(result["total_trades"], int)


@pytest.mark.asyncio
async def test_backtest_produces_equity_curve(ohlcv_data):
    """Verify equity curve has correct structure."""
    service = BacktestService()
    result = await service.run(
        strategy_name="sma_crossover",
        parameters={"fast_period": 10, "slow_period": 30},
        data=ohlcv_data,
        initial_capital=10000,
    )

    curve = result["equity_curve"]
    assert len(curve) == len(ohlcv_data)
    for point in curve[:5]:
        assert "timestamp" in point
        assert "equity" in point
        assert isinstance(point["equity"], float)
