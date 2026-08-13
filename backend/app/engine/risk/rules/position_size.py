"""
BETHBot — Position size risk rule.

Limits a single position to a percentage of total equity.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.execution.base import OrderRequest
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState


class PositionSizeRule(BaseRiskRule):
    """
    Limits position size as a percentage of total equity.
    Default: No single position > 20% of portfolio.
    """

    name = "position_size"
    priority = 1

    def __init__(self, max_position_pct: float = 0.20, max_position_size_pct: float | None = None):
        if max_position_size_pct is not None:
            self.max_position_pct = max_position_size_pct
        else:
            self.max_position_pct = max_position_pct

    def evaluate(
        self,
        order: OrderRequest,
        portfolio_state: PortfolioState,
        current_price: Decimal,
    ) -> RiskEvaluation:
        if portfolio_state.total_equity <= 0:
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason="Portfolio equity is zero or negative",
            )

        order_value = order.quantity * current_price
        max_allowed = portfolio_state.total_equity * Decimal(str(self.max_position_pct))

        # Include existing position value
        existing_qty = portfolio_state.positions.get(order.asset_symbol, Decimal("0"))
        existing_value = existing_qty * current_price
        total_exposure = existing_value + order_value

        if total_exposure > max_allowed:
            pct = float(total_exposure / portfolio_state.total_equity) * 100
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=(
                    f"REJECTED: Position size would be {pct:.1f}% of equity "
                    f"(max allowed: {self.max_position_pct * 100:.0f}%)."
                ),
            )

        return RiskEvaluation(
            decision=RiskDecision.APPROVED,
            rule_name=self.name,
            reason="Position size within limits",
        )
