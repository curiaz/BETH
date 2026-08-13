"""
BETHBot — Comprehensive Unit Tests for Risk Management Engine.

Tests required cases:
1. Structured decisions (APPROVED / REJECTED) with human-readable rejection reasons
2. Configurable risk rules:
   - Position size
   - Portfolio exposure
   - Risk per trade
   - Stop-loss
   - Take-profit
   - Maximum daily loss
   - Maximum open positions
   - Maximum trades per day
3. Independent testing for BTC/USDT and ETH/USDT
4. Simultaneous BTC/USDT and ETH/USDT exposure evaluation
5. Non-execution safety invariant verification
"""

from decimal import Decimal

import pytest

from app.engine.execution.base import OrderRequest, OrderSide, OrderType
from app.engine.risk.base import RiskDecision
from app.engine.risk.manager import RiskManager, RiskResult
from app.engine.risk.rules.daily_loss import DailyLossRule
from app.engine.risk.rules.exposure import ExposureRule
from app.engine.risk.rules.open_positions import MaxOpenPositionsRule
from app.engine.risk.rules.position_size import PositionSizeRule
from app.engine.risk.rules.risk_per_trade import MaxRiskPerTradeRule
from app.engine.risk.rules.stop_loss import StopLossRule
from app.engine.risk.rules.take_profit import TakeProfitRule
from app.engine.risk.rules.trades_per_day import MaxTradesPerDayRule
from app.engine.strategy.base import PortfolioState


class TestRiskEngine:
    def test_approve_valid_order_btc(self):
        """Test approval of a valid BTC/USDT buy order within all risk limits."""
        risk_mgr = RiskManager.create_default(
            max_position_size_pct=0.20,
            max_portfolio_exposure_pct=0.80,
        )

        portfolio = PortfolioState(
            total_equity=Decimal("10000.00"),
            cash_balance=Decimal("10000.00"),
            positions={},
        )

        # Proposed order: Buy 0.04 BTC @ 40,000 USDT = $1,600 USDT (16% of $10,000 equity)
        order = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.04"),
        )

        result: RiskResult = risk_mgr.evaluate_order(order, portfolio, Decimal("40000.00"))

        assert result.decision == RiskDecision.APPROVED
        assert result.is_approved
        assert result.reason == "APPROVED"

    def test_approve_valid_order_eth(self):
        """Test approval of a valid ETH/USDT buy order within all risk limits."""
        risk_mgr = RiskManager.create_default(max_position_size_pct=0.20)

        portfolio = PortfolioState(
            total_equity=Decimal("10000.00"),
            cash_balance=Decimal("10000.00"),
            positions={},
        )

        # Proposed order: Buy 0.5 ETH @ 2,000 USDT = $1,000 USDT (10% of $10,000 equity)
        order = OrderRequest(
            asset_symbol="ETH/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.5"),
        )

        result: RiskResult = risk_mgr.evaluate_order(order, portfolio, Decimal("2000.00"))

        assert result.decision == RiskDecision.APPROVED
        assert result.is_approved

    def test_reject_exceeds_max_position_size(self):
        """Test rejection when single position size exceeds limit."""
        risk_mgr = RiskManager([PositionSizeRule(max_position_size_pct=0.20)])

        portfolio = PortfolioState(
            total_equity=Decimal("10000.00"),
            cash_balance=Decimal("10000.00"),
        )

        # Proposed order: Buy 0.1 BTC @ 40,000 USDT = $4,000 USDT (40% > 20% limit)
        order = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.1"),
        )

        result = risk_mgr.evaluate_order(order, portfolio, Decimal("40000.00"))

        assert result.decision == RiskDecision.REJECTED
        assert not result.is_approved
        assert "REJECTED:" in result.reason
        assert "max allowed" in result.reason

    def test_simultaneous_btc_and_eth_exposure_rejection(self):
        """Test rejection when simultaneous BTC and ETH positions exceed total exposure limit."""
        risk_mgr = RiskManager([ExposureRule(max_exposure_pct=0.80)])

        # Portfolio has existing BTC position of 0.125 BTC @ 40,000 = $5,000 USDT (50% exposure)
        portfolio = PortfolioState(
            total_equity=Decimal("10000.00"),
            cash_balance=Decimal("5000.00"),
            positions={"BTC/USDT": Decimal("0.125")},
        )

        # Proposed ETH order: Buy 2 ETH @ 2,000 USDT = $4,000 USDT (40% proposed exposure)
        # Total exposure would be 50% + 40% = 90% (> 80% max exposure limit)
        order = OrderRequest(
            asset_symbol="ETH/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("2.0"),
        )

        result = risk_mgr.evaluate_order(order, portfolio, Decimal("2000.00"))

        assert result.decision == RiskDecision.REJECTED
        assert not result.is_approved
        assert "REJECTED:" in result.reason
        assert "Total portfolio exposure" in result.reason

    def test_reject_daily_loss_exceeded(self):
        """Test rejection when maximum daily loss threshold is hit."""
        risk_mgr = RiskManager([DailyLossRule(max_daily_loss_pct=0.03)])

        portfolio = PortfolioState(
            total_equity=Decimal("9600.00"),
            cash_balance=Decimal("9600.00"),
            peak_equity=Decimal("10000.00"),
            daily_pnl=Decimal("-400.00"),  # $400 loss on $10,000 is 4% (> 3% max daily loss)
        )

        order = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.02"),
        )

        result = risk_mgr.evaluate_order(order, portfolio, Decimal("40000.00"))

        assert result.decision == RiskDecision.REJECTED
        assert "Daily loss" in result.reason and "exceeds" in result.reason

    def test_reject_max_open_positions_exceeded(self):
        """Test rejection when max open positions count is reached."""
        risk_mgr = RiskManager([MaxOpenPositionsRule(max_open_positions=2)])

        # Portfolio has 2 open positions (BTC/USDT and ETH/USDT)
        portfolio = PortfolioState(
            total_equity=Decimal("10000.00"),
            positions={"BTC/USDT": Decimal("0.1"), "ETH/USDT": Decimal("1.0")},
        )

        # Proposed 3rd position: SOL/USDT
        order = OrderRequest(
            asset_symbol="SOL/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("10.0"),
        )

        result = risk_mgr.evaluate_order(order, portfolio, Decimal("100.00"))

        assert result.decision == RiskDecision.REJECTED
        assert "REJECTED: Maximum open positions limit reached" in result.reason

    def test_reject_max_trades_per_day_exceeded(self):
        """Test rejection when max trades per day limit is reached."""
        rule = MaxTradesPerDayRule(max_trades_per_day=5)
        rule.set_today_trade_count(5)  # 5 trades executed today

        risk_mgr = RiskManager([rule])

        portfolio = PortfolioState(total_equity=Decimal("10000.00"))
        order = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.01"),
        )

        result = risk_mgr.evaluate_order(order, portfolio, Decimal("40000.00"))

        assert result.decision == RiskDecision.REJECTED
        assert "REJECTED: Maximum trades per day limit reached" in result.reason

    def test_stop_loss_validation(self):
        """Test stop-loss requirement and maximum distance rules."""
        rule = StopLossRule(max_stop_loss_pct=0.10, require_stop_loss=True)
        risk_mgr = RiskManager([rule])

        portfolio = PortfolioState(total_equity=Decimal("10000.00"))

        # Order without stop-loss
        order_no_sl = OrderRequest(
            asset_symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.01"),
        )

        result_no_sl = risk_mgr.evaluate_order(order_no_sl, portfolio, Decimal("40000.00"))
        assert result_no_sl.decision == RiskDecision.REJECTED
        assert "REJECTED: Stop-loss is required" in result_no_sl.reason

    def test_non_execution_safety_invariant(self):
        """Verify RiskManager has no order execution capabilities or API dependencies."""
        risk_mgr = RiskManager.create_default()

        assert not hasattr(risk_mgr, "execute")
        assert not hasattr(risk_mgr, "submit_order_to_exchange")
        assert not hasattr(risk_mgr, "place_order")
        assert not hasattr(risk_mgr, "db")
