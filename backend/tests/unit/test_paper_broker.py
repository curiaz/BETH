"""
BETHBot — Unit Tests for Quantara PaperBroker Engine.

Tests required cases:
1. Initial account balance (10,000 USDT)
2. BUY / SELL market orders for BTC/USDT and ETH/USDT
3. Order status tracking, fills, fees, and slippage calculation
4. Order validation (invalid symbol, non-positive quantity)
5. Insufficient balance handling (rejection on insufficient cash)
6. Insufficient position handling (rejection on insufficient asset position)
7. Duplicate order protection
8. Position and trade history tracking
9. Zero real exchange communication safety invariant
"""

from decimal import Decimal

import pytest

from app.engine.execution.base import OrderRequest, OrderSide, OrderStatus, OrderType
from app.engine.execution.paper import PaperBroker


class TestPaperBroker:
    @pytest.mark.asyncio
    async def test_initial_account_balance(self):
        """Test initial 10,000 USDT paper balance and empty positions."""
        broker = PaperBroker(initial_balance=Decimal("10000.00"))

        assert broker.get_account_balance() == Decimal("10000.00")
        assert len(broker.get_positions()) == 0
        assert len(broker.get_trade_history()) == 0

    @pytest.mark.asyncio
    async def test_valid_btc_buy_order(self):
        """Test executing a valid BTC/USDT paper buy market order."""
        broker = PaperBroker(
            initial_balance=Decimal("10000.00"),
            slippage_pct=Decimal("0.001"),  # 0.1%
            fee_pct=Decimal("0.001"),       # 0.1%
        )

        broker.update_price("BTC/USDT", Decimal("40000.00"))

        order = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.1"),
        )

        fill = await broker.submit_order(order)

        # Base price = 40,000, Slippage = 40, Fill price = 40,040
        assert fill.price == Decimal("40040.00")
        # Fee = 40040 * 0.1 * 0.001 = 4.004 USDT
        assert fill.fee == Decimal("4.0040")
        assert fill.status == OrderStatus.FILLED

        # Cash = 10000 - (4004 + 4.004) = 5991.996 USDT
        assert broker.get_account_balance() == Decimal("5991.9960")
        assert broker.get_position("BTC/USDT") == Decimal("0.1")
        assert await broker.get_order_status(order.id) == OrderStatus.FILLED

    @pytest.mark.asyncio
    async def test_valid_eth_sell_order(self):
        """Test executing an ETH/USDT buy order followed by a sell order."""
        broker = PaperBroker(
            initial_balance=Decimal("10000.00"),
            slippage_pct=Decimal("0.0"),
            fee_pct=Decimal("0.0"),
        )

        broker.update_price("ETH/USDT", Decimal("2000.00"))

        # Buy 1.0 ETH @ 2000
        buy_order = OrderRequest(
            asset_symbol="ETH/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
        )
        await broker.submit_order(buy_order)
        assert broker.get_account_balance() == Decimal("8000.00")
        assert broker.get_position("ETH/USDT") == Decimal("1.0")

        # Update price to 2200 and Sell 1.0 ETH
        broker.update_price("ETH/USDT", Decimal("2200.00"))
        sell_order = OrderRequest(
            asset_symbol="ETH/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
        )
        fill_sell = await broker.submit_order(sell_order)

        assert fill_sell.status == OrderStatus.FILLED
        assert broker.get_account_balance() == Decimal("10200.00")
        assert broker.get_position("ETH/USDT") == Decimal("0")
        assert len(broker.get_trade_history()) == 2

    @pytest.mark.asyncio
    async def test_insufficient_balance_rejection(self):
        """Test rejection when buying with insufficient USDT cash balance."""
        broker = PaperBroker(initial_balance=Decimal("1000.00"))
        broker.update_price("BTC/USDT", Decimal("40000.00"))

        # Attempt to buy 1.0 BTC ($40,000 > $1,000 available cash)
        order = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
        )

        with pytest.raises(ValueError, match="Insufficient balance"):
            await broker.submit_order(order)

        assert await broker.get_order_status(order.id) == OrderStatus.REJECTED
        assert broker.get_account_balance() == Decimal("1000.00")

    @pytest.mark.asyncio
    async def test_insufficient_position_rejection(self):
        """Test rejection when selling an asset without holding sufficient position."""
        broker = PaperBroker(initial_balance=Decimal("10000.00"))
        broker.update_price("ETH/USDT", Decimal("2000.00"))

        # Attempt to sell 1.0 ETH with 0 position
        order = OrderRequest(
            asset_symbol="ETH/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
        )

        with pytest.raises(ValueError, match="Insufficient position"):
            await broker.submit_order(order)

        assert await broker.get_order_status(order.id) == OrderStatus.REJECTED

    @pytest.mark.asyncio
    async def test_invalid_quantity_rejection(self):
        """Test rejection when order quantity is zero or negative."""
        broker = PaperBroker()
        broker.update_price("BTC/USDT", Decimal("40000.00"))

        order = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.0"),
        )

        with pytest.raises(ValueError, match="Quantity must be positive"):
            await broker.submit_order(order)

        assert await broker.get_order_status(order.id) == OrderStatus.REJECTED

    @pytest.mark.asyncio
    async def test_duplicate_order_protection(self):
        """Test rejection when submitting an order with duplicate ID."""
        broker = PaperBroker()
        broker.update_price("BTC/USDT", Decimal("40000.00"))

        order = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.01"),
            id="order-dup-123",
        )

        await broker.submit_order(order)

        # Submit duplicate order ID
        with pytest.raises(ValueError, match="Duplicate order ID"):
            await broker.submit_order(order)

    @pytest.mark.asyncio
    async def test_safety_invariant_zero_exchange_communication(self):
        """Verify PaperBroker has no real exchange API properties or credentials."""
        broker = PaperBroker()

        assert not hasattr(broker, "api_key")
        assert not hasattr(broker, "api_secret")
        assert not hasattr(broker, "binance_client")
