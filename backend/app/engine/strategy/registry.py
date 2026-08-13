"""
BETHBot — Strategy registry.

Discovers and manages strategy classes. Strategies register themselves
via the @register decorator or are registered programmatically.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.engine.strategy.base import BaseStrategy

logger = get_logger(__name__)


class StrategyRegistry:
    """
    Singleton registry for all trading strategies.

    Usage:
        @StrategyRegistry.register
        class MyStrategy(BaseStrategy):
            name = "my_strategy"
            ...

    Or programmatically:
        StrategyRegistry.register_strategy(MyStrategy)
    """

    _strategies: dict[str, type[BaseStrategy]] = {}

    @classmethod
    def register(cls, strategy_class: type[BaseStrategy]) -> type[BaseStrategy]:
        """
        Register a strategy class. Can be used as a decorator.

        @StrategyRegistry.register
        class MyStrategy(BaseStrategy):
            ...
        """
        name = strategy_class.name
        if name in cls._strategies:
            logger.warning(
                "strategy.registry.overwrite",
                strategy=name,
                old_class=cls._strategies[name].__name__,
                new_class=strategy_class.__name__,
            )
        cls._strategies[name] = strategy_class
        logger.info("strategy.registered", strategy=name, version=strategy_class.version)
        return strategy_class

    @classmethod
    def register_strategy(cls, strategy_class: type[BaseStrategy]) -> None:
        """Register a strategy class programmatically."""
        cls.register(strategy_class)

    @classmethod
    def get(cls, name: str) -> type[BaseStrategy]:
        """
        Get a strategy class by name.

        Raises:
            KeyError: If strategy is not registered.
        """
        if name not in cls._strategies:
            available = list(cls._strategies.keys())
            raise KeyError(
                f"Strategy '{name}' not found. Available: {available}"
            )
        return cls._strategies[name]

    @classmethod
    def list_all(cls) -> dict[str, type[BaseStrategy]]:
        """Return all registered strategies."""
        return dict(cls._strategies)

    @classmethod
    def list_names(cls) -> list[str]:
        """Return names of all registered strategies."""
        return list(cls._strategies.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered strategies (for testing)."""
        cls._strategies.clear()

    @classmethod
    def initialize_builtin(cls) -> None:
        """
        Import and register all built-in strategies.
        Call this during application startup.
        """
        # Importing triggers @register decorators
        from app.engine.strategy.builtin import sma_crossover  # noqa: F401
        from app.engine.strategy.builtin import rsi_mean_reversion  # noqa: F401

        logger.info(
            "strategy.registry.initialized",
            count=len(cls._strategies),
            strategies=cls.list_names(),
        )
