"""
BETHBot — RSI Mean Reversion strategy.

A mean-reversion strategy that buys when RSI indicates oversold conditions
and sells when RSI indicates overbought conditions.
"""

from __future__ import annotations

import numpy as np
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
class RSIMeanReversion(BaseStrategy):
    """
    RSI Mean Reversion strategy.

    BUY when RSI drops below oversold threshold (default 30).
    SELL when RSI rises above overbought threshold (default 70).
    """

    name = "rsi_mean_reversion"
    version = "1.0.0"
    description = "RSI Mean Reversion — buys oversold, sells overbought"

    def __init__(
        self,
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ):
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self._prev_rsi: float | None = None

    @classmethod
    def parameters(cls) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                name="rsi_period",
                type=ParameterType.INT,
                default=14,
                min_value=2,
                max_value=50,
                description="RSI calculation period",
            ),
            ParameterSpec(
                name="oversold",
                type=ParameterType.FLOAT,
                default=30.0,
                min_value=10.0,
                max_value=40.0,
                description="RSI oversold threshold (buy signal)",
            ),
            ParameterSpec(
                name="overbought",
                type=ParameterType.FLOAT,
                default=70.0,
                min_value=60.0,
                max_value=90.0,
                description="RSI overbought threshold (sell signal)",
            ),
        ]

    @staticmethod
    def _compute_rsi(close: pd.Series, period: int) -> pd.Series:
        """Compute RSI manually (no pandas-ta dependency in engine)."""
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        # Use Wilder's smoothing after initial SMA
        for i in range(period, len(close)):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi

    def initialize(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """Add RSI column to the dataframe."""
        df = historical_data.copy()
        df["rsi"] = self._compute_rsi(df["close"].astype(float), self.rsi_period)
        return df

    def on_bar(self, bar: pd.Series, portfolio_state: PortfolioState) -> Signal:
        """Generate signal based on RSI levels."""
        rsi = bar.get("rsi")

        if rsi is None or pd.isna(rsi):
            return HOLD_SIGNAL

        rsi_val = float(rsi)
        signal = HOLD_SIGNAL

        # Oversold → BUY (mean reversion expects price to bounce up)
        if rsi_val <= self.oversold:
            # Stronger signal the more oversold
            strength = min(1.0, (self.oversold - rsi_val) / self.oversold)
            signal = Signal(
                direction=SignalDirection.BUY,
                strength=round(0.5 + strength * 0.5, 2),
                confidence=round(0.6 + strength * 0.3, 2),
                metadata={"trigger": "oversold", "rsi": rsi_val},
            )

        # Overbought → SELL (mean reversion expects price to drop)
        elif rsi_val >= self.overbought:
            strength = min(1.0, (rsi_val - self.overbought) / (100.0 - self.overbought))
            signal = Signal(
                direction=SignalDirection.SELL,
                strength=round(0.5 + strength * 0.5, 2),
                confidence=round(0.6 + strength * 0.3, 2),
                metadata={"trigger": "overbought", "rsi": rsi_val},
            )

        self._prev_rsi = rsi_val
        return signal

    def get_state(self) -> dict:
        return {"prev_rsi": self._prev_rsi}

    def set_state(self, state: dict) -> None:
        self._prev_rsi = state.get("prev_rsi")

    def reset(self) -> None:
        self._prev_rsi = None
