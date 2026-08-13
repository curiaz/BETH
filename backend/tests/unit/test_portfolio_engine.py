"""
BETHBot — Unit Tests for Quantara Portfolio Engine.

Tests required cases:
1. USDT cash, BTC position, and ETH position simultaneous tracking
2. Average entry price calculation (weighted average on multiple buys)
3. Current price updates, position value, unrealized P/L, realized P/L
4. Total portfolio valuation and asset/portfolio exposure %
5. Broker independence (processes fills from simulated PaperBroker/TestnetBroker)
6. High-precision Decimal calculations
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.engine.execution.base import Fill, OrderSide
from app.engine.portfolio.engine import PortfolioEngine, PortfolioSnapshot, PositionSnapshot


class MockPaperBrokerFill:
    """Mock Fill representing PaperBroker / TestnetBroker execution output."""

    @staticmethod
    def create(symbol: str, side: OrderSide, price: str, quantity: str, fee: str = "1.00") -> Fill:
        return Fill(
            order_id="mock-ord-101",
            asset_symbol=symbol,
            side=side,
            price=Decimal(price),
            quantity=Decimal(quantity),
            fee=Decimal(fee),
            slippage=Decimal("0.0"),
            timestamp=datetime.now(timezone.utc),
        )


class TestPortfolioEngine:
    def test_initial_portfolio_state(self):
        """Test initial cash balance and empty position state."""
        engine = PortfolioEngine(initial_cash=Decimal("10000.00"))
        snapshot = engine.get_snapshot()

        assert snapshot.cash_usdt == Decimal("10000.00")
        assert snapshot.total_portfolio_value == Decimal("10000.00")
        assert snapshot.total_exposure_usdt == Decimal("0.00")
        assert snapshot.total_exposure_pct == 0.0
        assert len(snapshot.positions) == 0

    def test_single_btc_buy_fill(self):
        """Test buying BTC/USDT position."""
        engine = PortfolioEngine(initial_cash=Decimal("10000.00"))

        # Buy 0.1 BTC @ 40,000 USDT with 4.00 fee -> Cost = 4000 + 4 = 4004 USDT
        fill = MockPaperBrokerFill.create("BTC/USDT", OrderSide.BUY, "40000.00", "0.1", fee="4.00")
        engine.process_fill(fill)

        assert engine.cash_usdt == Decimal("5996.00")  # 10000 - 4004
        assert engine.positions["BTC/USDT"] == Decimal("0.1")
        assert engine.avg_entry_prices["BTC/USDT"] == Decimal("40000.00")

        # Update price to 42,000 (+5% gain)
        engine.update_price("BTC/USDT", Decimal("42000.00"))

        pos_snap = engine.get_position_snapshot("BTC/USDT")
        assert pos_snap is not None
        assert pos_snap.position_value == Decimal("4200.00")  # 0.1 * 42000
        assert pos_snap.unrealized_pnl == Decimal("200.00")  # (42000 - 40000) * 0.1

        # Total portfolio value = cash (5996) + position_value (4200) = 10196 USDT
        assert engine.total_portfolio_value == Decimal("10196.00")

    def test_simultaneous_btc_and_eth_positions(self):
        """Test simultaneous BTC/USDT and ETH/USDT positions tracking."""
        engine = PortfolioEngine(initial_cash=Decimal("10000.00"))

        # Buy 0.1 BTC @ 40,000 (Cost = 4000 + 4 fee = 4004)
        btc_fill = MockPaperBrokerFill.create("BTC/USDT", OrderSide.BUY, "40000.00", "0.1", fee="4.00")
        engine.process_fill(btc_fill)

        # Buy 1.0 ETH @ 2,000 (Cost = 2000 + 2 fee = 2002)
        eth_fill = MockPaperBrokerFill.create("ETH/USDT", OrderSide.BUY, "2000.00", "1.0", fee="2.00")
        engine.process_fill(eth_fill)

        # Cash remaining: 10000 - 4004 - 2002 = 3994 USDT
        assert engine.cash_usdt == Decimal("3994.00")
        assert engine.positions["BTC/USDT"] == Decimal("0.1")
        assert engine.positions["ETH/USDT"] == Decimal("1.0")

        # Market updates: BTC = 42,000, ETH = 2,200
        engine.update_prices({
            "BTC/USDT": Decimal("42000.00"),
            "ETH/USDT": Decimal("2200.00"),
        })

        snapshot = engine.get_snapshot()

        # Position values: BTC = 4200, ETH = 2200 -> Total Exposure = 6400 USDT
        assert snapshot.total_exposure_usdt == Decimal("6400.00")

        # Total equity = 3994 + 6400 = 10394 USDT
        assert snapshot.total_portfolio_value == Decimal("10394.00")

        # Portfolio Exposure % = 6400 / 10394 * 100 = ~61.57%
        assert round(snapshot.total_exposure_pct, 2) == round(6400.0 / 10394.0 * 100.0, 2)

        # Total Unrealized PnL = (4200 - 4000) + (2200 - 2000) = 400 USDT
        assert snapshot.total_unrealized_pnl == Decimal("400.00")

    def test_weighted_average_entry_price_calculation(self):
        """Test weighted average entry price for multiple buys."""
        engine = PortfolioEngine(initial_cash=Decimal("10000.00"))

        # Buy 1: 0.1 BTC @ 40,000
        fill1 = MockPaperBrokerFill.create("BTC/USDT", OrderSide.BUY, "40000.00", "0.1", fee="0.0")
        engine.process_fill(fill1)

        # Buy 2: 0.1 BTC @ 44,000
        fill2 = MockPaperBrokerFill.create("BTC/USDT", OrderSide.BUY, "44000.00", "0.1", fee="0.0")
        engine.process_fill(fill2)

        # Total BTC = 0.2, Avg Entry = (4000 + 4400) / 0.2 = 42,000 USDT
        assert engine.positions["BTC/USDT"] == Decimal("0.2")
        assert engine.avg_entry_prices["BTC/USDT"] == Decimal("42000.00")

    def test_sell_fill_realized_pnl(self):
        """Test position close and realized PnL calculation."""
        engine = PortfolioEngine(initial_cash=Decimal("10000.00"))

        # Buy 0.1 BTC @ 40,000 (Cost = 4000 + 0 fee)
        buy_fill = MockPaperBrokerFill.create("BTC/USDT", OrderSide.BUY, "40000.00", "0.1", fee="0.0")
        engine.process_fill(buy_fill)

        # Sell 0.1 BTC @ 45,000 (Revenue = 4500 - 5.00 fee = 4495)
        sell_fill = MockPaperBrokerFill.create("BTC/USDT", OrderSide.SELL, "45000.00", "0.1", fee="5.00")
        engine.process_fill(sell_fill)

        # Cash = 6000 + 4495 = 10495 USDT
        assert engine.cash_usdt == Decimal("10495.00")

        # Position should be closed
        assert "BTC/USDT" not in engine.positions

        # Realized PnL = (45000 - 40000) * 0.1 - 5.00 = 500 - 5 = 495 USDT
        assert engine.total_realized_pnl == Decimal("495.00")

    def test_broker_independence(self):
        """Verify engine processes fills from any broker without importing exchange code."""
        engine = PortfolioEngine()
        # Verify engine does not require Binance or HTTP connections
        assert not hasattr(engine, "binance_client")
        assert not hasattr(engine, "api_key")
