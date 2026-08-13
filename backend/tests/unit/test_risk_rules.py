"""
BETHBot — Unit tests: Risk rules.
"""

from decimal import Decimal

from app.engine.execution.base import OrderRequest, OrderSide, OrderType
from app.engine.risk.base import RiskDecision
from app.engine.risk.manager import RiskManager
from app.engine.risk.rules.daily_loss import DailyLossRule
from app.engine.risk.rules.exposure import ExposureRule
from app.engine.risk.rules.max_drawdown import MaxDrawdownRule
from app.engine.risk.rules.position_size import PositionSizeRule
from app.engine.strategy.base import PortfolioState


def _make_order(symbol: str = "BTC/USDT", quantity: float = 0.1, side: OrderSide = OrderSide.BUY) -> OrderRequest:
    return OrderRequest(
        asset_symbol=symbol,
        side=side,
        order_type=OrderType.MARKET,
        quantity=Decimal(str(quantity)),
    )


def _make_portfolio(
    equity: float = 10000,
    cash: float = 10000,
    peak: float = 10000,
    daily_pnl: float = 0,
    positions: dict | None = None,
) -> PortfolioState:
    return PortfolioState(
        total_equity=Decimal(str(equity)),
        cash_balance=Decimal(str(cash)),
        peak_equity=Decimal(str(peak)),
        positions={k: Decimal(str(v)) for k, v in (positions or {}).items()},
        daily_pnl=Decimal(str(daily_pnl)),
    )


class TestPositionSizeRule:
    def test_approve_within_limits(self):
        rule = PositionSizeRule(max_position_pct=0.20)
        order = _make_order(quantity=0.04)  # 0.04 * 42000 = 1680 < 2000 (20% of 10000)
        portfolio = _make_portfolio()
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        assert result.decision == RiskDecision.APPROVED

    def test_reject_exceeds_limit(self):
        rule = PositionSizeRule(max_position_pct=0.20)
        order = _make_order(quantity=0.1)  # 0.1 * 42000 = 4200 > 2000
        portfolio = _make_portfolio()
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        assert result.decision == RiskDecision.REJECTED

    def test_includes_existing_position(self):
        rule = PositionSizeRule(max_position_pct=0.20)
        order = _make_order(quantity=0.02)  # New: 0.02 * 42000 = 840
        portfolio = _make_portfolio(positions={"BTC/USDT": 0.03})  # Existing: 0.03 * 42000 = 1260
        # Total: 2100 > 2000
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        assert result.decision == RiskDecision.REJECTED


class TestMaxDrawdownRule:
    def test_approve_no_drawdown(self):
        rule = MaxDrawdownRule(max_drawdown_pct=0.15)
        order = _make_order()
        portfolio = _make_portfolio(equity=10000, peak=10000)
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        assert result.decision == RiskDecision.APPROVED

    def test_reject_excessive_drawdown(self):
        rule = MaxDrawdownRule(max_drawdown_pct=0.15)
        order = _make_order()
        portfolio = _make_portfolio(equity=8000, peak=10000)  # 20% drawdown
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        assert result.decision == RiskDecision.REJECTED

    def test_approve_within_drawdown_limit(self):
        rule = MaxDrawdownRule(max_drawdown_pct=0.15)
        order = _make_order()
        portfolio = _make_portfolio(equity=9000, peak=10000)  # 10% drawdown
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        assert result.decision == RiskDecision.APPROVED


class TestDailyLossRule:
    def test_approve_no_loss(self):
        rule = DailyLossRule(max_daily_loss_pct=0.03)
        order = _make_order()
        portfolio = _make_portfolio(daily_pnl=100)
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        assert result.decision == RiskDecision.APPROVED

    def test_reject_excessive_daily_loss(self):
        rule = DailyLossRule(max_daily_loss_pct=0.03)
        order = _make_order()
        portfolio = _make_portfolio(daily_pnl=-400)  # 4% loss on 10000
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        assert result.decision == RiskDecision.REJECTED


class TestExposureRule:
    def test_approve_within_limits(self):
        rule = ExposureRule(max_exposure_pct=0.80)
        order = _make_order(quantity=0.1)
        portfolio = _make_portfolio()  # No existing positions
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        # 0.1 * 42000 = 4200 < 8000 (80% of 10000)
        assert result.decision == RiskDecision.APPROVED

    def test_reject_exceeds_exposure(self):
        rule = ExposureRule(max_exposure_pct=0.80)
        order = _make_order(quantity=0.2)
        portfolio = _make_portfolio()
        # 0.2 * 42000 = 8400 > 8000
        result = rule.evaluate(order, portfolio, Decimal("42000"))
        assert result.decision == RiskDecision.REJECTED


class TestRiskManager:
    def test_all_approved(self):
        manager = RiskManager([
            PositionSizeRule(0.50),
            MaxDrawdownRule(0.15),
        ])
        order = _make_order(quantity=0.01)
        portfolio = _make_portfolio()
        evaluations = manager.evaluate(order, portfolio, Decimal("42000"))
        assert RiskManager.is_approved(evaluations)
        assert len(evaluations) == 2

    def test_one_rejection_fails(self):
        manager = RiskManager([
            PositionSizeRule(0.01),  # Very restrictive
            MaxDrawdownRule(0.15),
        ])
        order = _make_order(quantity=0.1)
        portfolio = _make_portfolio()
        evaluations = manager.evaluate(order, portfolio, Decimal("42000"))
        assert not RiskManager.is_approved(evaluations)

    def test_get_rejections(self):
        manager = RiskManager([
            PositionSizeRule(0.01),
        ])
        order = _make_order(quantity=0.1)
        portfolio = _make_portfolio()
        evaluations = manager.evaluate(order, portfolio, Decimal("42000"))
        rejections = RiskManager.get_rejections(evaluations)
        assert len(rejections) == 1
        assert "position_size" in rejections[0].rule_name
