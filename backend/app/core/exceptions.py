"""
BETHBot — Custom exception hierarchy.

All trading-specific exceptions inherit from TradingError.
FastAPI exception handlers map these to appropriate HTTP status codes.
"""

from __future__ import annotations


class BETHBotError(Exception):
    """Base exception for all BETHBot errors."""

    def __init__(self, message: str = "An unexpected error occurred"):
        self.message = message
        super().__init__(self.message)


# --- Trading Errors ---


class TradingError(BETHBotError):
    """Base exception for trading-related errors."""

    pass


class InsufficientFundsError(TradingError):
    """Raised when there isn't enough capital to execute an order."""

    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient funds: required {required:.2f}, available {available:.2f}"
        )


class RiskViolationError(TradingError):
    """Raised when an order violates risk management rules."""

    def __init__(self, rule_name: str, reason: str):
        self.rule_name = rule_name
        self.reason = reason
        super().__init__(f"Risk violation [{rule_name}]: {reason}")


class OrderError(TradingError):
    """Raised for order lifecycle errors (invalid state transitions, etc.)."""

    pass


class PositionError(TradingError):
    """Raised for position management errors."""

    pass


# --- Data Errors ---


class DataError(BETHBotError):
    """Base exception for data-related errors."""

    pass


class MarketDataError(DataError):
    """Raised when market data fetch or processing fails."""

    pass


class InvalidSymbolError(DataError):
    """Raised when a symbol format is malformed or invalid."""

    def __init__(self, symbol: str, reason: str = "Invalid symbol format"):
        self.symbol = symbol
        self.reason = reason
        super().__init__(f"Invalid symbol '{symbol}': {reason}")


class UnsupportedSymbolError(InvalidSymbolError):
    """Raised when a requested symbol is valid in format but not enabled in configuration."""

    def __init__(self, symbol: str, supported: list[str] | None = None):
        self.symbol = symbol
        self.supported = supported or []
        msg = f"Unsupported symbol '{symbol}'"
        if supported:
            msg += f". Currently supported: {', '.join(supported)}"
        super().__init__(symbol, reason=msg)


# --- Integration Errors ---


class IntegrationError(BETHBotError):
    """Base exception for external service errors."""

    pass


class ExchangeError(IntegrationError):
    """Raised when exchange API communication fails."""

    def __init__(self, exchange: str, message: str):
        self.exchange = exchange
        super().__init__(f"Exchange error [{exchange}]: {message}")


class NotificationError(IntegrationError):
    """Raised when notification delivery fails."""

    pass


# --- Configuration Errors ---


class ConfigurationError(BETHBotError):
    """Raised for invalid configuration."""

    pass


class LiveTradingDisabledError(TradingError):
    """Raised when live trading is attempted in Phase 1."""

    def __init__(self) -> None:
        super().__init__(
            "Live trading is disabled. "
            "BETHBot Phase 1 supports backtest and paper trading only."
        )


# --- Strategy Errors ---


class StrategyError(BETHBotError):
    """Base exception for strategy-related errors."""

    pass


class StrategyNotFoundError(StrategyError):
    """Raised when a requested strategy is not registered."""

    def __init__(self, name: str, available: list[str] | None = None):
        self.strategy_name = name
        self.available = available or []
        msg = f"Strategy not found: {name}"
        if available:
            msg += f". Available: {', '.join(available)}"
        super().__init__(msg)
