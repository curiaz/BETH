"""
BETHBot — Core Domain Enums.

Defines all standard domain enums for orders, signals, positions, and execution modes.
"""

from __future__ import annotations

from enum import StrEnum


class OrderSide(StrEnum):
    """Side of an order (BUY or SELL)."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    """Type of an order (MARKET or LIMIT)."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(StrEnum):
    """Lifecycle status of an order."""

    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Signal(StrEnum):
    """Direction/side of a strategy signal."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# Alias for backward compatibility with existing engine/strategy code
SignalDirection = Signal


class PositionSide(StrEnum):
    """Side of an open position."""

    LONG = "LONG"
    SHORT = "SHORT"


class PositionStatus(StrEnum):
    """Status of a position."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class AssetType(StrEnum):
    """Type of asset or instrument."""

    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"
    FUTURES = "FUTURES"
