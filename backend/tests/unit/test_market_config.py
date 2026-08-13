"""
BETHBot — Unit Tests for Asset & Market Configuration System.

Tests required cases:
1. BTC/USDT validation and retrieval
2. ETH/USDT validation and retrieval
3. Unsupported symbol handling (e.g. DOGE/USDT)
4. Invalid symbol format handling (e.g. malformed or empty)
5. Multiple symbols handling (list or comma-separated string)
6. Extensible asset registration without changing business logic
"""

from decimal import Decimal

import pytest

from app.core.exceptions import InvalidSymbolError, UnsupportedSymbolError
from app.core.market_config import MarketRegistry, market_registry
from app.domain.enums import AssetType
from app.domain.models import Market


class TestMarketConfigSystem:
    def test_btc_usdt_support(self):
        """Verify BTC/USDT validation and retrieval."""
        registry = MarketRegistry()
        symbol = registry.validate_symbol("BTC/USDT", active_symbols=["BTC/USDT", "ETH/USDT"])
        assert symbol == "BTC/USDT"

        market = registry.get_market("BTC/USDT", active_symbols=["BTC/USDT", "ETH/USDT"])
        assert market.symbol == "BTC/USDT"
        assert market.base_asset == "BTC"
        assert market.quote_asset == "USDT"
        assert market.tick_size == Decimal("0.01")
        assert market.lot_size == Decimal("0.00001")

    def test_eth_usdt_support(self):
        """Verify ETH/USDT validation and retrieval."""
        registry = MarketRegistry()
        symbol = registry.validate_symbol("ETH/USDT", active_symbols=["BTC/USDT", "ETH/USDT"])
        assert symbol == "ETH/USDT"

        market = registry.get_market("ETH/USDT", active_symbols=["BTC/USDT", "ETH/USDT"])
        assert market.symbol == "ETH/USDT"
        assert market.base_asset == "ETH"
        assert market.quote_asset == "USDT"
        assert market.lot_size == Decimal("0.0001")

    def test_lowercase_symbol_normalization(self):
        """Verify lowercase symbol string normalization (e.g., 'btc/usdt')."""
        registry = MarketRegistry()
        assert registry.validate_symbol("btc/usdt", active_symbols=["BTC/USDT"]) == "BTC/USDT"
        assert registry.validate_symbol("ethusdt", active_symbols=["ETH/USDT"]) == "ETH/USDT"

    def test_unsupported_symbol(self):
        """Verify unsupported symbols raise UnsupportedSymbolError."""
        registry = MarketRegistry()

        # DOGE/USDT is not in standard catalog/config
        with pytest.raises(UnsupportedSymbolError) as exc_info:
            registry.validate_symbol("DOGE/USDT", active_symbols=["BTC/USDT", "ETH/USDT"])

        assert exc_info.value.symbol == "DOGE/USDT"
        assert "BTC/USDT" in str(exc_info.value)

    def test_invalid_symbol_format(self):
        """Verify malformed symbol format raises InvalidSymbolError."""
        registry = MarketRegistry()

        with pytest.raises(InvalidSymbolError):
            registry.validate_symbol("INVALID_FORMAT_NO_SLASH_AND_TOO_LONG_SYMBOL_NAME")

        with pytest.raises(InvalidSymbolError):
            registry.validate_symbol("")

        with pytest.raises(InvalidSymbolError):
            registry.validate_symbol("A/B")  # Too short (1 char)

    def test_multiple_symbols_validation(self):
        """Verify validating multiple symbols from list or comma-separated string."""
        registry = MarketRegistry()
        active = ["BTC/USDT", "ETH/USDT"]

        # String format
        result1 = registry.validate_symbols("BTC/USDT, ETH/USDT", active_symbols=active)
        assert result1 == ["BTC/USDT", "ETH/USDT"]

        # List format
        result2 = registry.validate_symbols(["btc/usdt", "eth/usdt"], active_symbols=active)
        assert result2 == ["BTC/USDT", "ETH/USDT"]

    def test_multiple_symbols_with_one_unsupported(self):
        """Verify validating multiple symbols fails if any symbol is unsupported."""
        registry = MarketRegistry()
        active = ["BTC/USDT", "ETH/USDT"]

        with pytest.raises(UnsupportedSymbolError):
            registry.validate_symbols("BTC/USDT, SOL/USDT", active_symbols=active)

    def test_extensible_future_asset_registration(self):
        """Verify registering a new market dynamically without modifying trading logic."""
        registry = MarketRegistry()

        # Create new Market definition for SOL/USDT
        sol_market = Market(
            symbol="SOL/USDT",
            base_asset="SOL",
            quote_asset="USDT",
            exchange="binance",
            asset_type=AssetType.SPOT,
            tick_size=Decimal("0.01"),
            lot_size=Decimal("0.01"),
            min_notional=Decimal("10.0"),
        )

        # Register market
        registry.register_market(sol_market)

        # Validate with SOL/USDT included in active config
        active_config = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        validated = registry.validate_symbol("SOL/USDT", active_symbols=active_config)
        assert validated == "SOL/USDT"

        market = registry.get_market("SOL/USDT", active_symbols=active_config)
        assert market.base_asset == "SOL"
        assert market.quote_asset == "USDT"

    def test_get_supported_markets(self):
        """Verify fetching all supported Market models for configured active symbols."""
        registry = MarketRegistry()
        active = ["BTC/USDT", "ETH/USDT"]

        supported_markets = registry.get_supported_markets(active_symbols=active)
        assert len(supported_markets) == 2
        symbols = [m.symbol for m in supported_markets]
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols
