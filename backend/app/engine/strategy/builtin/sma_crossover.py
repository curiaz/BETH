"""
BETHBot — SMA Crossover strategy.

A classic momentum strategy that generates BUY signals when
the fast SMA crosses above the slow SMA, and SELL signals
when it crosses below.
"""

from __future__ import annotations

import pandas as pd

from app.engine.strategy.base import (
    BaseStrategy,
    HOLD_SIGNAL,
    ParameterSpec,
    ParameterType,
    PortfolioState,
    Signal,
    SignalDirection,
)
from app.engine.strategy.registry import StrategyRegistry


@StrategyRegistry.register
class SMACrossover(BaseStrategy):
    """
    Simple Moving Average Crossover strategy.

    BUY when fast SMA crosses above slow SMA (golden cross).
    SELL when fast SMA crosses below slow SMA (death cross).
    """

    name = "sma_crossover"
    version = "1.0.0"
    description = "SMA Crossover — buys on golden cross, sells on death cross"

    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self._prev_fast: float | None = None
        self._prev_slow: float | None = None

    @classmethod
    def parameters(cls) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                name="fast_period",
                type=ParameterType.INT,
                default=20,
                min_value=5,
                max_value=100,
                description="Fast SMA period",
            ),
            ParameterSpec(
                name="slow_period",
                type=ParameterType.INT,
                default=50,
                min_value=10,
                max_value=200,
                description="Slow SMA period",
            ),
        ]

    def initialize(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """Add SMA columns to the dataframe."""
        df = historical_data.copy()
        df["sma_fast"] = df["close"].rolling(window=self.fast_period).mean()
        df["sma_slow"] = df["close"].rolling(window=self.slow_period).mean()
        return df

    def on_bar(self, bar: pd.Series, portfolio_state: PortfolioState) -> Signal:
        """Generate signal based on SMA crossover."""
        fast = bar.get("sma_fast")
        slow = bar.get("sma_slow")

        # Not enough data for indicators
        if fast is None or slow is None or pd.isna(fast) or pd.isna(slow):
            return HOLD_SIGNAL

        signal = HOLD_SIGNAL

        if self._prev_fast is not None and self._prev_slow is not None:
            # Bullish crossover: fast crosses above slow
            if self._prev_fast <= self._prev_slow and fast > slow:
                signal = Signal(
                    direction=SignalDirection.BUY,
                    strength=0.8,
                    confidence=0.7,
                    metadata={"trigger": "golden_cross", "sma_fast": fast, "sma_slow": slow},
                )
            # Bearish crossover: fast crosses below slow
            elif self._prev_fast >= self._prev_slow and fast < slow:
                signal = Signal(
                    direction=SignalDirection.SELL,
                    strength=0.8,
                    confidence=0.7,
                    metadata={"trigger": "death_cross", "sma_fast": fast, "sma_slow": slow},
                )

        self._prev_fast = float(fast)
        self._prev_slow = float(slow)
        return signal

    def get_state(self) -> dict:
        return {
            "prev_fast": self._prev_fast,
            "prev_slow": self._prev_slow,
        }

    def set_state(self, state: dict) -> None:
        self._prev_fast = state.get("prev_fast")
        self._prev_slow = state.get("prev_slow")

    def reset(self) -> None:
        self._prev_fast = None
        self._prev_slow = None
