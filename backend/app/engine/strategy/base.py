"""
BETHBot — Base strategy module (re-exports framework types).
"""

from app.engine.strategy.framework import (
    ParameterSpec,
    ParameterType,
    PortfolioState,
    SignalDirection,
    SignalResult,
    Strategy,
    StrategyConfiguration,
    StrategyContext,
)

# Backward compatibility aliases
BaseStrategy = Strategy
Signal = SignalResult
HOLD_SIGNAL = SignalResult(direction=SignalDirection.HOLD, strength=0.0, confidence=0.0)

__all__ = [
    "BaseStrategy",
    "Strategy",
    "Signal",
    "SignalResult",
    "SignalDirection",
    "HOLD_SIGNAL",
    "ParameterSpec",
    "ParameterType",
    "PortfolioState",
    "StrategyConfiguration",
    "StrategyContext",
]
