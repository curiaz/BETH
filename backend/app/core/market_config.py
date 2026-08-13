"""
BETHBot — Centralized Market & Asset Configuration System.

Manages market definitions for supported instruments (BTC/USDT, ETH/USDT, etc.)
and validates symbols against environment and application configuration.
Future assets can be added by registering new Market definitions without
modifying any trading logic or strategy implementations.
"""

from __future__ import annotations

import re
from decimal import Decimal

from app.core.config import settings
from app.core.exceptions import InvalidSymbolError, UnsupportedSymbolError
from app.domain.enums import AssetType
from app.domain.models import Market

# Regex for market symbol validation (e.g. BTC/USDT)
MARKET_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,10}/[A-Z0-9]{2,10}$")


# Built-in Market Catalog definitions
DEFAULT_MARKET_CATALOG: dict[str, Market] = {
    "BTC/USDT": Market(
        symbol="BTC/USDT",
        base_asset="BTC",
        quote_asset="USDT",
        exchange="binance",
        asset_type=AssetType.SPOT,
        tick_size=Decimal("0.01"),
        lot_size=Decimal("0.00001"),
        min_notional=Decimal("10.0"),
        maker_fee=Decimal("0.001"),
        taker_fee=Decimal("0.001"),
        is_active=True,
    ),
    "ETH/USDT": Market(
        symbol="ETH/USDT",
        base_asset="ETH",
        quote_asset="USDT",
        exchange="binance",
        asset_type=AssetType.SPOT,
        tick_size=Decimal("0.01"),
        lot_size=Decimal("0.0001"),
        min_notional=Decimal("10.0"),
        maker_fee=Decimal("0.001"),
        taker_fee=Decimal("0.001"),
        is_active=True,
    ),
}


class MarketRegistry:
    """
    Centralized Market Configuration Manager.

    Provides symbol normalization, format validation, environment-based asset enablement,
    and dynamic market registration for future asset expansion.
    """

    def __init__(self, catalog: dict[str, Market] | None = None):
        self._catalog: dict[str, Market] = dict(catalog or DEFAULT_MARKET_CATALOG)

    def register_market(self, market: Market) -> None:
        """
        Register a new market definition dynamically.
        Enables adding new trading pairs without modifying core logic.
        """
        self._catalog[market.symbol] = market

    def get_catalog(self) -> dict[str, Market]:
        """Return all registered market definitions in the catalog."""
        return dict(self._catalog)

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize raw symbol input to standard 'BASE/QUOTE' format.
        Supports inputs like 'btc/usdt', 'BTC/USDT', 'BTCUSDT', 'ethusdt'.
        """
        if not symbol or not isinstance(symbol, str):
            raise InvalidSymbolError(str(symbol), reason="Symbol must be a non-empty string")

        clean = symbol.strip().upper()

        # Handle 'BTC/USDT'
        if "/" in clean:
            return clean

        # Handle un-slashed symbols like 'BTCUSDT' or 'ETHUSDT' by checking catalog keys
        for key in self._catalog:
            if key.replace("/", "") == clean:
                return key

        # If un-slashed and not in catalog, try heuristic split if standard quote currency (USDT, USD, BTC, ETH)
        for quote in ("USDT", "BUSD", "USDC", "USD", "BTC", "ETH"):
            if clean.endswith(quote) and len(clean) > len(quote):
                base = clean[: -len(quote)]
                return f"{base}/{quote}"

        return clean

    def is_format_valid(self, symbol: str) -> bool:
        """Check if symbol format matches 'BASE/QUOTE' structure."""
        try:
            normalized = self.normalize_symbol(symbol)
            return bool(MARKET_SYMBOL_PATTERN.match(normalized))
        except InvalidSymbolError:
            return False

    def validate_symbol(
        self,
        symbol: str,
        active_symbols: list[str] | None = None,
    ) -> str:
        """
        Validate that a symbol is correctly formatted AND supported in configuration.

        Args:
            symbol: The symbol string to validate
            active_symbols: Optional list of configured active symbols.
                           If None, defaults to settings.symbols_list.

        Returns:
            Normalized symbol string (e.g. "BTC/USDT")

        Raises:
            InvalidSymbolError: If symbol format is invalid
            UnsupportedSymbolError: If symbol is valid format but not configured/supported
        """
        try:
            normalized = self.normalize_symbol(symbol)
        except Exception as e:
            raise InvalidSymbolError(symbol, reason=str(e)) from e

        if not MARKET_SYMBOL_PATTERN.match(normalized):
            raise InvalidSymbolError(
                symbol,
                reason=f"Symbol '{normalized}' does not match standard 'BASE/QUOTE' format.",
            )

        configured_symbols = (
            active_symbols if active_symbols is not None else settings.symbols_list
        )
        configured_set = {s.strip().upper() for s in configured_symbols if s.strip()}

        if normalized not in self._catalog or normalized not in configured_set:
            raise UnsupportedSymbolError(normalized, supported=list(configured_set))

        return normalized

    def validate_symbols(
        self,
        symbols: str | list[str],
        active_symbols: list[str] | None = None,
    ) -> list[str]:
        """
        Validate multiple symbols (passed as a list or comma-separated string).
        Returns a list of validated normalized symbols.
        """
        if isinstance(symbols, str):
            raw_list = [s.strip() for s in symbols.split(",") if s.strip()]
        else:
            raw_list = symbols

        if not raw_list:
            raise InvalidSymbolError("", reason="At least one symbol must be provided")

        validated = []
        for s in raw_list:
            norm = self.validate_symbol(s, active_symbols=active_symbols)
            validated.append(norm)

        return validated

    def is_symbol_supported(
        self,
        symbol: str,
        active_symbols: list[str] | None = None,
    ) -> bool:
        """Check if symbol is valid and supported without throwing exceptions."""
        try:
            self.validate_symbol(symbol, active_symbols=active_symbols)
            return True
        except (InvalidSymbolError, UnsupportedSymbolError):
            return False

    def get_market(
        self,
        symbol: str,
        active_symbols: list[str] | None = None,
    ) -> Market:
        """
        Retrieve Market domain model for a validated symbol.

        Raises:
            InvalidSymbolError or UnsupportedSymbolError if invalid or unsupported.
        """
        normalized = self.validate_symbol(symbol, active_symbols=active_symbols)
        return self._catalog[normalized]

    def get_supported_markets(
        self,
        active_symbols: list[str] | None = None,
    ) -> list[Market]:
        """
        Get Market models for all currently supported/enabled symbols in config.
        """
        configured_symbols = (
            active_symbols if active_symbols is not None else settings.symbols_list
        )
        configured_set = {s.strip().upper() for s in configured_symbols if s.strip()}

        markets = []
        for sym in configured_set:
            if sym in self._catalog:
                markets.append(self._catalog[sym])
        return markets


# Global singleton instance for application use
market_registry = MarketRegistry()
