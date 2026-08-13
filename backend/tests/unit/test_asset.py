"""
BETHBot — Unit tests: Asset abstraction.
"""

from decimal import Decimal

from app.engine.asset import AssetType, TradingPair


class TestTradingPair:
    def test_from_symbol(self):
        pair = TradingPair.from_symbol("BTC/USDT")
        assert pair.symbol == "BTC/USDT"
        assert pair.base == "BTC"
        assert pair.quote == "USDT"
        assert pair.exchange == "binance"
        assert pair.asset_type == AssetType.SPOT

    def test_round_price(self):
        pair = TradingPair.from_symbol("BTC/USDT")
        pair = pair.model_copy(update={"tick_size": Decimal("0.01")})
        assert pair.round_price(Decimal("42123.456")) == Decimal("42123.45")

    def test_round_quantity(self):
        pair = TradingPair.from_symbol("BTC/USDT")
        pair = pair.model_copy(update={"lot_size": Decimal("0.001")})
        assert pair.round_quantity(Decimal("1.23456")) == Decimal("1.234")

    def test_validate_order_valid(self):
        pair = TradingPair.from_symbol("BTC/USDT")
        pair = pair.model_copy(update={"min_notional": Decimal("10.0")})
        valid, reason = pair.validate_order(Decimal("42000"), Decimal("0.001"))
        assert valid
        assert reason == "OK"

    def test_validate_order_below_min_notional(self):
        pair = TradingPair.from_symbol("BTC/USDT")
        pair = pair.model_copy(update={"min_notional": Decimal("10.0")})
        valid, reason = pair.validate_order(Decimal("42000"), Decimal("0.0001"))
        assert not valid
        assert "below minimum" in reason

    def test_validate_order_zero_quantity(self):
        pair = TradingPair.from_symbol("BTC/USDT")
        valid, reason = pair.validate_order(Decimal("42000"), Decimal("0"))
        assert not valid

    def test_calculate_fee(self):
        pair = TradingPair.from_symbol("BTC/USDT")
        pair = pair.model_copy(update={"taker_fee": Decimal("0.001")})
        fee = pair.calculate_fee(Decimal("42000"), Decimal("1.0"), is_maker=False)
        assert fee == Decimal("42.000")

    def test_invalid_symbol_format(self):
        import pytest

        with pytest.raises(ValueError, match="Invalid symbol format"):
            TradingPair.from_symbol("BTCUSDT")
