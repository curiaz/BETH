"""
BETHBot — Unit Tests for Strategy Framework and Moving Average Crossover Strategy.

Tests required cases:
1. StrategyConfiguration validation and parameter parsing
2. StrategyContext initialization
3. SignalResult immutability and is_actionable behavior
4. MovingAverageCrossoverStrategy with BTC/USDT (BUY, SELL, HOLD signals)
5. MovingAverageCrossoverStrategy with ETH/USDT (reusability without code duplication)
6. Configurable fast and slow periods
7. Encapsulation verification (no API/order/DB access)
"""

from datetime import datetime, timezone
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from app.domain.enums import Signal
from app.engine.strategy.builtin.sma_crossover import MovingAverageCrossoverStrategy
from app.engine.strategy.framework import (
    SignalResult,
    Strategy,
    StrategyConfiguration,
    StrategyContext,
)


class TestStrategyFrameworkTypes:
    def test_strategy_configuration_defaults(self):
        """Test StrategyConfiguration initialization and defaults."""
        config = StrategyConfiguration(
            strategy_name="sma_crossover",
            parameters={"fast_period": 10, "slow_period": 30},
        )
        assert config.strategy_name == "sma_crossover"
        assert config.parameters["fast_period"] == 10
        assert "BTC/USDT" in config.supported_symbols
        assert "ETH/USDT" in config.supported_symbols

    def test_strategy_context_initialization(self):
        """Test StrategyContext initialization."""
        now = datetime.now(timezone.utc)
        context = StrategyContext(
            symbol="BTC/USDT",
            timeframe="1h",
            indicators={"sma_fast": 42000.0, "sma_slow": 41500.0},
            timestamp=now,
        )
        assert context.symbol == "BTC/USDT"
        assert context.timeframe == "1h"
        assert context.indicators["sma_fast"] == 42000.0
        assert context.timestamp == now

    def test_signal_result_behavior(self):
        """Test SignalResult immutability and is_actionable helper."""
        now = datetime.now(timezone.utc)

        hold_signal = SignalResult(
            symbol="BTC/USDT",
            direction=Signal.HOLD,
            timestamp=now,
        )
        assert not hold_signal.is_actionable

        buy_signal = SignalResult(
            symbol="BTC/USDT",
            direction=Signal.BUY,
            strength=0.85,
            confidence=0.75,
            timestamp=now,
        )
        assert buy_signal.is_actionable
        assert buy_signal.direction == Signal.BUY

        # Test immutability
        with pytest.raises(AttributeError):
            buy_signal.direction = Signal.SELL  # type: ignore


class TestMovingAverageCrossoverStrategy:
    def _create_sample_ohlcv(self, prices: list[float]) -> pd.DataFrame:
        dates = pd.date_range(start="2024-01-01", periods=len(prices), freq="h", tz="UTC")
        return pd.DataFrame(
            {
                "open": prices,
                "high": [p * 1.01 for p in prices],
                "low": [p * 0.99 for p in prices],
                "close": prices,
                "volume": [100.0] * len(prices),
            },
            index=dates,
        )

    def test_strategy_initialization_btc_usdt(self):
        """Test MA Crossover initialization for BTC/USDT."""
        strategy = MovingAverageCrossoverStrategy(fast_period=5, slow_period=10)
        assert strategy.fast_period == 5
        assert strategy.slow_period == 10

        prices = [40000.0 + i * 100 for i in range(20)]
        df = self._create_sample_ohlcv(prices)
        enriched = strategy.initialize(df)

        assert "sma_fast" in enriched.columns
        assert "sma_slow" in enriched.columns

    def test_generate_signal_golden_cross_btc(self):
        """Test Golden Cross (BUY signal) generation for BTC/USDT."""
        strategy = MovingAverageCrossoverStrategy(fast_period=3, slow_period=5)

        # Bar 1: Fast (40) <= Slow (40)
        ctx1 = StrategyContext(
            symbol="BTC/USDT",
            indicators={"sma_fast": 40000.0, "sma_slow": 40000.0},
        )
        sig1 = strategy.generate_signal(ctx1)
        assert sig1.direction == Signal.HOLD

        # Bar 2: Fast (41000) > Slow (40500) -> Golden Cross -> BUY
        ctx2 = StrategyContext(
            symbol="BTC/USDT",
            indicators={"sma_fast": 41000.0, "sma_slow": 40500.0},
        )
        sig2 = strategy.generate_signal(ctx2)
        assert sig2.direction == Signal.BUY
        assert sig2.symbol == "BTC/USDT"
        assert sig2.metadata["trigger"] == "golden_cross"

    def test_generate_signal_death_cross_eth(self):
        """Test Death Cross (SELL signal) generation for ETH/USDT without code duplication."""
        strategy = MovingAverageCrossoverStrategy(fast_period=3, slow_period=5)

        # Bar 1: Fast (2200) >= Slow (2150)
        ctx1 = StrategyContext(
            symbol="ETH/USDT",
            indicators={"sma_fast": 2200.0, "sma_slow": 2150.0},
        )
        sig1 = strategy.generate_signal(ctx1)
        assert sig1.direction == Signal.HOLD

        # Bar 2: Fast (2100) < Slow (2150) -> Death Cross -> SELL
        ctx2 = StrategyContext(
            symbol="ETH/USDT",
            indicators={"sma_fast": 2100.0, "sma_slow": 2150.0},
        )
        sig2 = strategy.generate_signal(ctx2)
        assert sig2.direction == Signal.SELL
        assert sig2.symbol == "ETH/USDT"
        assert sig2.metadata["trigger"] == "death_cross"

    def test_generate_signal_hold_when_no_crossover(self):
        """Test HOLD signal when fast MA remains above slow MA without crossing."""
        strategy = MovingAverageCrossoverStrategy(fast_period=3, slow_period=5)

        ctx1 = StrategyContext(symbol="BTC/USDT", indicators={"sma_fast": 42000.0, "sma_slow": 40000.0})
        strategy.generate_signal(ctx1)

        ctx2 = StrategyContext(symbol="BTC/USDT", indicators={"sma_fast": 42500.0, "sma_slow": 40500.0})
        sig2 = strategy.generate_signal(ctx2)
        assert sig2.direction == Signal.HOLD

    def test_configurable_periods(self):
        """Test that fast_period and slow_period parameters can be customized."""
        strategy = MovingAverageCrossoverStrategy(fast_period=10, slow_period=30)
        assert strategy.fast_period == 10
        assert strategy.slow_period == 30

    def test_encapsulation_rules(self):
        """Verify strategy does NOT have order submission or external API methods."""
        strategy = MovingAverageCrossoverStrategy()

        assert not hasattr(strategy, "place_order")
        assert not hasattr(strategy, "submit_order")
        assert not hasattr(strategy, "execute_trade")
        assert not hasattr(strategy, "db_session")
        assert not hasattr(strategy, "api_client")
