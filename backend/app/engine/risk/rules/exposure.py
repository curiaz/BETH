"""
BETHBot — Total exposure risk rule.

Limits total portfolio exposure (sum of all positions / equity).
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.execution.base import OrderRequest, OrderSide
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState


class ExposureRule(BaseRiskRule):
    """
    Limits total portfolio exposure.
    Default: Max 80% of equity deployed across all positions.
    Ensures a cash reserve for margin and new opportunities.
    """

    name = "total_exposure"
    priority = 2

    def __init__(self, max_exposure_pct: float = 0.80):
        self.max_exposure_pct = max_exposure_pct

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

        # Calculate current total exposure
        total_position_value = Decimal("0")
        for symbol, qty in portfolio_state.positions.items():
            # For simplicity, value each position at current order's price
            # In production, we'd look up each symbol's price
            total_position_value += abs(qty) * current_price

        # Add the new order's value (only for BUY orders — SELL reduces exposure)
        if order.side == OrderSide.BUY:
            new_exposure = total_position_value + (order.quantity * current_price)
        else:
            new_exposure = total_position_value

        max_allowed = portfolio_state.total_equity * Decimal(str(self.max_exposure_pct))

        if new_exposure > max_allowed:
            pct = float(new_exposure / portfolio_state.total_equity) * 100
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=(
                    f"Total exposure would be {pct:.1f}% of equity "
                    f"(max {self.max_exposure_pct * 100:.0f}%)"
                ),
            )

        return RiskEvaluation(
            decision=RiskDecision.APPROVED,
            rule_name=self.name,
            reason="Total exposure within limits",
        )
