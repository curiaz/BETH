"""
BETHBot — Moving Average Crossover Strategy.

Implementation of the Moving Average Crossover strategy within the Strategy framework.
Supports configurable fast and slow periods, works with both BTC/USDT and ETH/USDT
without duplicate strategy code.

Generates BUY, SELL, or HOLD signals strictly — does NOT place orders, access APIs,
or modify portfolio/database state.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.domain.enums import Signal
from app.engine.strategy.base import ParameterSpec, ParameterType
from app.engine.strategy.framework import (
    SignalResult,
    Strategy,
    StrategyConfiguration,
    StrategyContext,
)
from app.engine.strategy.registry import StrategyRegistry


@StrategyRegistry.register
class MovingAverageCrossoverStrategy(Strategy):
    """
    Moving Average Crossover Strategy.

    BUY signal when fast moving average crosses above slow moving average (golden cross).
    SELL signal when fast moving average crosses below slow moving average (death cross).
    HOLD when no crossover occurs or indicators are incomplete.
    """

    name = "sma_crossover"
    version = "1.0.0"
    description = "Moving Average Crossover strategy — buys on golden cross, sells on death cross"

    def __init__(
        self,
        fast_period: int = 20,
        slow_period: int = 50,
        ma_type: str = "SMA",
        config: StrategyConfiguration | dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        params = {"fast_period": fast_period, "slow_period": slow_period, "ma_type": ma_type}
        if kwargs:
            params.update(kwargs)
        if isinstance(config, dict):
            params.update(config)

        super().__init__(config=params)

        self.fast_period = int(self.configuration.parameters.get("fast_period", fast_period))
        self.slow_period = int(self.configuration.parameters.get("slow_period", slow_period))
        self.ma_type = str(self.configuration.parameters.get("ma_type", ma_type)).upper()

        self._prev_fast: float | None = None
        self._prev_slow: float | None = None

    @classmethod
    def parameters(cls) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                name="fast_period",
                type=ParameterType.INT,
                default=20,
                min_value=2,
                max_value=100,
                description="Fast moving average period",
            ),
            ParameterSpec(
                name="slow_period",
                type=ParameterType.INT,
                default=50,
                min_value=5,
                max_value=200,
                description="Slow moving average period",
            ),
        ]

    def initialize(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving average indicators on historical close prices."""
        df = historical_data.copy()

        if self.ma_type == "EMA":
            df["sma_fast"] = df["close"].ewm(span=self.fast_period, adjust=False).mean()
            df["sma_slow"] = df["close"].ewm(span=self.slow_period, adjust=False).mean()
        else:
            df["sma_fast"] = df["close"].rolling(window=self.fast_period).mean()
            df["sma_slow"] = df["close"].rolling(window=self.slow_period).mean()

        return df

    def generate_signal(self, context: StrategyContext) -> SignalResult:
        """
        Generate BUY, SELL, or HOLD signal based on moving average crossover.

        Args:
            context: StrategyContext containing market indicators and metadata

        Returns:
            SignalResult with direction (BUY, SELL, HOLD), strength, and confidence
        """
        symbol = context.symbol

        # Extract indicators from context or candle Series
        fast = context.indicators.get("sma_fast")
        slow = context.indicators.get("sma_slow")

        if fast is None or slow is None:
            if isinstance(context.candle, pd.Series):
                fast = context.candle.get("sma_fast")
                slow = context.candle.get("sma_slow")

        if fast is None or slow is None or pd.isna(fast) or pd.isna(slow):
            return SignalResult(
                symbol=symbol,
                direction=Signal.HOLD,
                strength=0.0,
                confidence=0.0,
                timestamp=context.timestamp,
                metadata={"reason": "Insufficient indicator data"},
            )

        fast_val = float(fast)
        slow_val = float(slow)

        direction = Signal.HOLD
        strength = 0.0
        confidence = 0.5
        trigger = "none"

        if self._prev_fast is not None and self._prev_slow is not None:
            # Golden Cross: Fast crosses ABOVE Slow
            if self._prev_fast <= self._prev_slow and fast_val > slow_val:
                direction = Signal.BUY
                strength = 0.85
                confidence = 0.75
                trigger = "golden_cross"

            # Death Cross: Fast crosses BELOW Slow
            elif self._prev_fast >= self._prev_slow and fast_val < slow_val:
                direction = Signal.SELL
                strength = 0.85
                confidence = 0.75
                trigger = "death_cross"

        self._prev_fast = fast_val
        self._prev_slow = slow_val

        return SignalResult(
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=confidence,
            timestamp=context.timestamp,
            metadata={
                "trigger": trigger,
                "sma_fast": fast_val,
                "sma_slow": slow_val,
                "fast_period": self.fast_period,
                "slow_period": self.slow_period,
            },
        )

    def get_state(self) -> dict[str, Any]:
        return {"prev_fast": self._prev_fast, "prev_slow": self._prev_slow}

    def set_state(self, state: dict[str, Any]) -> None:
        self._prev_fast = state.get("prev_fast")
        self._prev_slow = state.get("prev_slow")

    def reset(self) -> None:
        self._prev_fast = None
        self._prev_slow = None


# Alias for backward compatibility
SMACrossover = MovingAverageCrossoverStrategy
