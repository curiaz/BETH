"""
BETHBot — Unit tests: Strategy base + SMA Crossover + RSI Mean Reversion.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.engine.strategy.base import (
    BaseStrategy,
    HOLD_SIGNAL,
    ParameterSpec,
    PortfolioState,
    Signal,
    SignalDirection,
)
from app.engine.strategy.registry import StrategyRegistry
from app.engine.strategy.builtin.sma_crossover import SMACrossover
from app.engine.strategy.builtin.rsi_mean_reversion import RSIMeanReversion


class TestSignal:
    def test_hold_signal_not_actionable(self):
        assert not HOLD_SIGNAL.is_actionable

    def test_buy_signal_is_actionable(self):
        signal = Signal(direction=SignalDirection.BUY, strength=0.8, confidence=0.7)
        assert signal.is_actionable

    def test_sell_signal_is_actionable(self):
        signal = Signal(direction=SignalDirection.SELL, strength=0.5, confidence=0.6)
        assert signal.is_actionable

    def test_signal_is_frozen(self):
        signal = Signal(direction=SignalDirection.HOLD)
        import pytest
        with pytest.raises(AttributeError):
            signal.direction = SignalDirection.BUY


class TestSMACrossover:
    def _make_data(self, n=100):
        np.random.seed(42)
        dates = pd.date_range(
            start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            periods=n,
            freq="h",
        )
        price = 42000.0
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

    def test_parameters(self):
        params = SMACrossover.parameters()
        assert len(params) == 2
        assert params[0].name == "fast_period"
        assert params[1].name == "slow_period"

    def test_initialize_adds_columns(self):
        strategy = SMACrossover(fast_period=5, slow_period=10)
        data = self._make_data(50)
        result = strategy.initialize(data)
        assert "sma_fast" in result.columns
        assert "sma_slow" in result.columns

    def test_on_bar_returns_signal(self):
        strategy = SMACrossover(fast_period=5, slow_period=10)
        data = self._make_data(50)
        data = strategy.initialize(data)
        portfolio = PortfolioState()

        # First bar should be HOLD (no previous data)
        signal = strategy.on_bar(data.iloc[0], portfolio)
        assert isinstance(signal, Signal)

    def test_get_set_state(self):
        strategy = SMACrossover()
        strategy._prev_fast = 42000.0
        strategy._prev_slow = 41000.0

        state = strategy.get_state()
        assert state["prev_fast"] == 42000.0

        strategy2 = SMACrossover()
        strategy2.set_state(state)
        assert strategy2._prev_fast == 42000.0

    def test_reset(self):
        strategy = SMACrossover()
        strategy._prev_fast = 42000.0
        strategy.reset()
        assert strategy._prev_fast is None


class TestRSIMeanReversion:
    def _make_data(self, n=100):
        np.random.seed(42)
        dates = pd.date_range(
            start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            periods=n,
            freq="h",
        )
        prices = [42000 + np.random.normal(0, 500) for _ in range(n)]
        return pd.DataFrame(
            {"open": prices, "high": prices, "low": prices, "close": prices, "volume": [100] * n},
            index=dates,
        )

    def test_parameters(self):
        params = RSIMeanReversion.parameters()
        assert len(params) == 3
        names = [p.name for p in params]
        assert "rsi_period" in names
        assert "oversold" in names
        assert "overbought" in names

    def test_initialize_adds_rsi(self):
        strategy = RSIMeanReversion(rsi_period=14)
        data = self._make_data(50)
        result = strategy.initialize(data)
        assert "rsi" in result.columns


class TestStrategyRegistry:
    def test_register_and_get(self):
        # Built-in strategies should be registered from imports above
        StrategyRegistry.initialize_builtin()
        assert "sma_crossover" in StrategyRegistry.list_names()
        assert "rsi_mean_reversion" in StrategyRegistry.list_names()

    def test_get_nonexistent(self):
        import pytest
        with pytest.raises(KeyError):
            StrategyRegistry.get("nonexistent_strategy")

    def test_list_all(self):
        StrategyRegistry.initialize_builtin()
        all_strategies = StrategyRegistry.list_all()
        assert len(all_strategies) >= 2
