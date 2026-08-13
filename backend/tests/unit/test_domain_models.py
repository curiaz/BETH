"""
BETHBot — Comprehensive Unit Tests for Core Domain Models.

Tests all 10 core domain models, validations, enums, calculations, and state transitions:
1. Asset
2. Market
3. Candle
4. Ticker
5. SignalModel
6. Order
7. Trade
8. Position
9. Portfolio
10. Account
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.enums import (
    AssetType,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSide,
    PositionStatus,
    Signal,
)
from app.domain.models import (
    Account,
    Asset,
    Candle,
    Market,
    Order,
    Portfolio,
    Position,
    SignalModel,
    Ticker,
    Trade,
)

# ============================================================================
# 1. Asset Tests
# ============================================================================


class TestAssetDomainModel:
    def test_valid_asset_creation(self):
        btc = Asset(code="BTC", name="Bitcoin", precision=8)
        assert btc.code == "BTC"
        assert btc.name == "Bitcoin"
        assert btc.precision == 8
        assert btc.asset_type == AssetType.SPOT

        eth = Asset(code="eth", name="Ethereum", precision=18)
        assert eth.code == "ETH"  # uppercase normalization

    def test_invalid_asset_code(self):
        with pytest.raises(ValidationError, match="Invalid asset code"):
            Asset(code="B", name="Short Code")

        with pytest.raises(ValidationError, match="Invalid asset code"):
            Asset(code="INVALID_LONG_CODE", name="Long Code")

    def test_asset_precision_bounds(self):
        with pytest.raises(ValidationError):
            Asset(code="BTC", name="Bitcoin", precision=20)

        with pytest.raises(ValidationError):
            Asset(code="BTC", name="Bitcoin", precision=-1)


# ============================================================================
# 2. Market Tests
# ============================================================================


class TestMarketDomainModel:
    def test_valid_market_creation(self):
        btc_usdt = Market(
            symbol="BTC/USDT",
            base_asset="BTC",
            quote_asset="USDT",
            tick_size=Decimal("0.01"),
            lot_size=Decimal("0.00001"),
            min_notional=Decimal("10.0"),
        )
        assert btc_usdt.symbol == "BTC/USDT"
        assert btc_usdt.base_asset == "BTC"
        assert btc_usdt.quote_asset == "USDT"

        eth_usdt = Market(
            symbol="ETH/USDT",
            base_asset="ETH",
            quote_asset="USDT",
            tick_size=Decimal("0.01"),
            lot_size=Decimal("0.0001"),
        )
        assert eth_usdt.symbol == "ETH/USDT"

    def test_market_symbol_mismatch(self):
        with pytest.raises(ValidationError, match="does not match base/quote"):
            Market(symbol="BTC/ETH", base_asset="BTC", quote_asset="USDT")

    def test_identical_base_quote(self):
        with pytest.raises(ValidationError, match="cannot be identical"):
            Market(symbol="USDT/USDT", base_asset="USDT", quote_asset="USDT")

    def test_non_positive_market_limits(self):
        with pytest.raises(ValidationError, match="strictly positive"):
            Market(symbol="BTC/USDT", base_asset="BTC", quote_asset="USDT", tick_size=Decimal("0"))

        with pytest.raises(ValidationError, match="strictly positive"):
            Market(symbol="BTC/USDT", base_asset="BTC", quote_asset="USDT", min_notional=Decimal("-5"))


# ============================================================================
# 3. Candle Tests
# ============================================================================


class TestCandleDomainModel:
    def test_valid_candle(self):
        now = datetime.now(timezone.utc)
        candle = Candle(
            symbol="BTC/USDT",
            timeframe="1h",
            open_time=now,
            close_time=now + timedelta(hours=1),
            open=Decimal("42000.00"),
            high=Decimal("42500.00"),
            low=Decimal("41800.00"),
            close=Decimal("42300.00"),
            volume=Decimal("12.5"),
        )
        assert candle.symbol == "BTC/USDT"
        assert candle.high >= candle.low

    def test_invalid_ohlc_high_lower_than_low(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError, match="High price .* cannot be less than low"):
            Candle(
                symbol="BTC/USDT",
                timeframe="1h",
                open_time=now,
                close_time=now + timedelta(hours=1),
                open=Decimal("42000.00"),
                high=Decimal("41000.00"),  # high < low
                low=Decimal("41800.00"),
                close=Decimal("42300.00"),
                volume=Decimal("10.0"),
            )

    def test_invalid_candle_timestamps(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError, match="Close time .* cannot be before open time"):
            Candle(
                symbol="BTC/USDT",
                timeframe="1h",
                open_time=now,
                close_time=now - timedelta(hours=1),
                open=Decimal("42000.00"),
                high=Decimal("42500.00"),
                low=Decimal("41800.00"),
                close=Decimal("42300.00"),
                volume=Decimal("10.0"),
            )


# ============================================================================
# 4. Ticker Tests
# ============================================================================


class TestTickerDomainModel:
    def test_valid_ticker(self):
        ticker = Ticker(
            symbol="BTC/USDT",
            last_price=Decimal("42100.00"),
            bid_price=Decimal("42095.00"),
            ask_price=Decimal("42105.00"),
            volume_24h=Decimal("1500.5"),
            high_24h=Decimal("43000.00"),
            low_24h=Decimal("41500.00"),
        )
        assert ticker.bid_price <= ticker.ask_price

    def test_invalid_ticker_bid_greater_than_ask(self):
        with pytest.raises(ValidationError, match="Bid price .* cannot exceed ask price"):
            Ticker(
                symbol="BTC/USDT",
                last_price=Decimal("42100.00"),
                bid_price=Decimal("42200.00"),  # bid > ask
                ask_price=Decimal("42100.00"),
            )


# ============================================================================
# 5. Signal Tests
# ============================================================================


class TestSignalDomainModel:
    def test_valid_signal(self):
        signal = SignalModel(
            symbol="BTC/USDT",
            direction=Signal.BUY,
            strength=0.85,
            confidence=0.90,
            target_price=Decimal("45000.00"),
            stop_loss=Decimal("40000.00"),
        )
        assert signal.direction == Signal.BUY
        assert signal.strength == 0.85

    def test_signal_strength_bounds(self):
        with pytest.raises(ValidationError):
            SignalModel(symbol="BTC/USDT", direction=Signal.BUY, strength=1.5)

        with pytest.raises(ValidationError):
            SignalModel(symbol="BTC/USDT", direction=Signal.SELL, confidence=-0.1)


# ============================================================================
# 6. Order Tests
# ============================================================================


class TestOrderDomainModel:
    def test_valid_limit_order(self):
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.5"),
            price=Decimal("42000.00"),
        )
        assert order.status == OrderStatus.PENDING
        assert order.price == Decimal("42000.00")

    def test_valid_market_order(self):
        order = Order(
            symbol="ETH/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("2.0"),
        )
        assert order.price is None

    def test_limit_order_requires_price(self):
        with pytest.raises(ValidationError, match="LIMIT orders require a price"):
            Order(
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=Decimal("0.5"),
                price=None,
            )

    def test_negative_quantity_rejected(self):
        with pytest.raises(ValidationError, match="strictly positive"):
            Order(
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("-1.0"),
            )

    def test_order_state_transitions(self):
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("40000.00"),
            status=OrderStatus.PENDING,
        )

        assert order.can_transition_to(OrderStatus.PARTIALLY_FILLED)
        assert order.can_transition_to(OrderStatus.FILLED)
        assert order.can_transition_to(OrderStatus.CANCELLED)
        assert order.can_transition_to(OrderStatus.REJECTED)

        # Terminal state transitions
        filled_order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("40000.00"),
            status=OrderStatus.FILLED,
        )
        assert not filled_order.can_transition_to(OrderStatus.PENDING)
        assert not filled_order.can_transition_to(OrderStatus.CANCELLED)


# ============================================================================
# 7. Trade Tests
# ============================================================================


class TestTradeDomainModel:
    def test_valid_trade(self):
        trade = Trade(
            order_id="ord-123",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=Decimal("42000.00"),
            quantity=Decimal("0.5"),
            fee=Decimal("4.20"),
            fee_currency="USDT",
        )
        assert trade.price == Decimal("42000.00")
        assert trade.quantity == Decimal("0.5")

    def test_trade_negative_price_rejected(self):
        with pytest.raises(ValidationError, match="strictly positive"):
            Trade(
                order_id="ord-123",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                price=Decimal("-100"),
                quantity=Decimal("1.0"),
            )


# ============================================================================
# 8. Position Tests
# ============================================================================


class TestPositionDomainModel:
    def test_long_position_pnl_calculation(self):
        pos = Position(
            symbol="BTC/USDT",
            side=PositionSide.LONG,
            quantity=Decimal("1.0"),
            entry_price=Decimal("40000.00"),
            current_price=Decimal("42000.00"),
        )
        unrealized = pos.calculate_unrealized_pnl()
        assert unrealized == Decimal("2000.00")

    def test_short_position_pnl_calculation(self):
        pos = Position(
            symbol="BTC/USDT",
            side=PositionSide.SHORT,
            quantity=Decimal("1.0"),
            entry_price=Decimal("40000.00"),
            current_price=Decimal("38000.00"),
        )
        unrealized = pos.calculate_unrealized_pnl()
        assert unrealized == Decimal("2000.00")


# ============================================================================
# 9. Portfolio Tests
# ============================================================================


class TestPortfolioDomainModel:
    def test_valid_portfolio(self):
        portfolio = Portfolio(
            account_id="acc-001",
            cash_balance=Decimal("10000.00"),
            total_equity=Decimal("12000.00"),
            unrealized_pnl=Decimal("2000.00"),
        )
        assert portfolio.cash_balance == Decimal("10000.00")

    def test_negative_cash_balance_rejected(self):
        with pytest.raises(ValidationError, match="cannot be negative"):
            Portfolio(account_id="acc-001", cash_balance=Decimal("-50.0"))


# ============================================================================
# 10. Account Tests
# ============================================================================


class TestAccountDomainModel:
    def test_valid_account(self):
        account = Account(
            name="Primary Trading Account",
            currency="USDT",
            balance=Decimal("10000.00"),
            available_balance=Decimal("8000.00"),
            locked_balance=Decimal("2000.00"),
        )
        assert account.balance == account.available_balance + account.locked_balance

    def test_account_balance_sum_mismatch(self):
        with pytest.raises(ValidationError, match="does not equal available .* locked"):
            Account(
                name="Primary Trading Account",
                currency="USDT",
                balance=Decimal("10000.00"),
                available_balance=Decimal("8000.00"),
                locked_balance=Decimal("3000.00"),  # Sum is 11000 != 10000
            )
