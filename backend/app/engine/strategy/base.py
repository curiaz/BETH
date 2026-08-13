"""
BETHBot — Abstract base strategy and signal types.

All trading strategies must inherit from BaseStrategy.
The engine layer has NO database or HTTP dependencies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any

import pandas as pd


class SignalDirection(StrEnum):
    """Trading signal direction."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Signal:
    """
    Immutable strategy output.

    A strategy processes a bar and returns a Signal indicating
    what action (if any) to take.
    """

    direction: SignalDirection
    strength: float = 0.0  # 0.0 to 1.0 — how strong the signal is
    confidence: float = 0.0  # 0.0 to 1.0 — how confident the strategy is
    target_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_actionable(self) -> bool:
        """Returns True if the signal suggests a trade (not HOLD)."""
        return self.direction != SignalDirection.HOLD


class ParameterType(StrEnum):
    """Supported parameter types for strategy configuration."""

    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"


@dataclass
class ParameterSpec:
    """
    Describes a strategy parameter for UI rendering and validation.
    Used by the frontend to dynamically build strategy configuration forms.
    """

    name: str
    type: ParameterType
    default: Any
    min_value: Any = None
    max_value: Any = None
    description: str = ""


@dataclass
class PortfolioState:
    """
    Simplified portfolio state passed to strategies.
    Strategies use this to make position-aware decisions.
    """

    total_equity: Decimal = Decimal("0")
    cash_balance: Decimal = Decimal("0")
    peak_equity: Decimal = Decimal("0")
    positions: dict[str, Decimal] = field(default_factory=dict)  # symbol → quantity
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    daily_pnl: Decimal = Decimal("0")


# Constant for HOLD signal to avoid repeated object creation
HOLD_SIGNAL = Signal(direction=SignalDirection.HOLD, strength=0.0, confidence=0.0)


class BaseStrategy(ABC):
    """
    Abstract base for all trading strategies.

    Lifecycle:
      1. __init__(params)         — set parameters
      2. initialize(data)         — pre-compute indicators on full history
      3. on_bar(bar, state)       — called for each new bar; return a Signal
      4. get_state() / set_state() — serialize/deserialize for persistence

    Rules:
      - Strategies must be deterministic given the same inputs
      - Strategies must NOT access external resources (DB, HTTP, files)
      - All external data comes in through method arguments
    """

    name: str = "unnamed"
    version: str = "1.0.0"
    description: str = ""

    @classmethod
    @abstractmethod
    def parameters(cls) -> list[ParameterSpec]:
        """
        Declare configurable parameters.

        These are used by:
          - The UI to build configuration forms
          - The backtester for parameter grid search
          - The registry for parameter validation
        """
        ...

    @abstractmethod
    def initialize(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Pre-compute indicators on historical data.

        Called once before bar-by-bar processing begins.
        Should add indicator columns to the DataFrame and return it.

        Args:
            historical_data: DataFrame with columns [open, high, low, close, volume]

        Returns:
            DataFrame with additional indicator columns
        """
        ...

    @abstractmethod
    def on_bar(self, bar: pd.Series, portfolio_state: PortfolioState) -> Signal:
        """
        Process a single bar and return a trading signal.

        Args:
            bar: Current OHLCV bar (plus any indicator columns from initialize())
            portfolio_state: Current portfolio state

        Returns:
            Signal with direction, strength, and optional price targets
        """
        ...

    def get_state(self) -> dict[str, Any]:
        """Serialize internal state for persistence across restarts."""
        return {}

    def set_state(self, state: dict[str, Any]) -> None:
        """Restore internal state from persistence."""
        pass

    def on_trade(self, trade_info: dict[str, Any]) -> None:
        """Optional callback when a trade is executed from this strategy's signal."""
        pass

    def reset(self) -> None:
        """Reset strategy to initial state. Called before each backtest run."""
        pass
