"""
BETHBot — RSI Mean Reversion strategy.

A mean-reversion strategy that buys when RSI indicates oversold conditions
and sells when RSI indicates overbought conditions.
"""

from __future__ import annotations

from typing import Any

import numpy as np
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
class RSIMeanReversion(Strategy):
    """
    RSI Mean Reversion strategy.

    BUY when RSI drops below oversold threshold (default 30).
    SELL when RSI rises above overbought threshold (default 70).
    HOLD when RSI is in neutral range.
    """

    name = "rsi_mean_reversion"
    version = "1.0.0"
    description = "RSI Mean Reversion — buys oversold, sells overbought"

    def __init__(
        self,
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        config: StrategyConfiguration | dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        params = {"rsi_period": rsi_period, "oversold": oversold, "overbought": overbought}
        if kwargs:
            params.update(kwargs)
        if isinstance(config, dict):
            params.update(config)

        super().__init__(config=params)

        self.rsi_period = int(self.configuration.parameters.get("rsi_period", rsi_period))
        self.oversold = float(self.configuration.parameters.get("oversold", oversold))
        self.overbought = float(self.configuration.parameters.get("overbought", overbought))
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
        """Compute RSI manually."""
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

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

    def generate_signal(self, context: StrategyContext) -> SignalResult:
        """Generate signal based on RSI threshold levels."""
        symbol = context.symbol
        rsi = context.indicators.get("rsi")

        if rsi is None and isinstance(context.candle, pd.Series):
            rsi = context.candle.get("rsi")

        if rsi is None or pd.isna(rsi):
            return SignalResult(
                symbol=symbol,
                direction=Signal.HOLD,
                strength=0.0,
                confidence=0.0,
                timestamp=context.timestamp,
                metadata={"reason": "Insufficient RSI data"},
            )

        rsi_val = float(rsi)
        direction = Signal.HOLD
        strength = 0.0
        confidence = 0.5
        trigger = "neutral"

        # Oversold → BUY
        if rsi_val <= self.oversold:
            s_ratio = min(1.0, (self.oversold - rsi_val) / self.oversold)
            direction = Signal.BUY
            strength = round(0.5 + s_ratio * 0.5, 2)
            confidence = round(0.6 + s_ratio * 0.3, 2)
            trigger = "oversold"

        # Overbought → SELL
        elif rsi_val >= self.overbought:
            s_ratio = min(1.0, (rsi_val - self.overbought) / (100.0 - self.overbought))
            direction = Signal.SELL
            strength = round(0.5 + s_ratio * 0.5, 2)
            confidence = round(0.6 + s_ratio * 0.3, 2)
            trigger = "overbought"

        self._prev_rsi = rsi_val

        return SignalResult(
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=confidence,
            timestamp=context.timestamp,
            metadata={"trigger": trigger, "rsi": rsi_val},
        )

    def get_state(self) -> dict[str, Any]:
        return {"prev_rsi": self._prev_rsi}

    def set_state(self, state: dict[str, Any]) -> None:
        self._prev_rsi = state.get("prev_rsi")

    def reset(self) -> None:
        self._prev_rsi = None
