"""
BETHBot — Take-Profit Validation Rule.

Validates that proposed buy orders have valid take-profit targets.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.execution.base import OrderRequest, OrderSide
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState


class TakeProfitRule(BaseRiskRule):
    """
    Validates take-profit target for buy orders.
    """

    name = "take_profit_validation"
    priority = 21

    def __init__(self, min_reward_risk_ratio: float = 1.0):
        self.min_reward_risk_ratio = min_reward_risk_ratio

    def evaluate(
        self,
        order: OrderRequest,
        portfolio_state: PortfolioState,
        current_price: Decimal,
    ) -> RiskEvaluation:
        if order.side != OrderSide.BUY:
            return RiskEvaluation(
                decision=RiskDecision.APPROVED,
                rule_name=self.name,
                reason="Sell orders do not require take-profit validation",
            )

        take_profit = getattr(order, "take_profit", None)
        if take_profit is None:
            return RiskEvaluation(
                decision=RiskDecision.APPROVED,
                rule_name=self.name,
                reason="No explicit take-profit provided; passing validation.",
            )

        tp_price = Decimal(str(take_profit))
        if tp_price <= current_price:
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=f"REJECTED: Take-profit price ({tp_price}) must be above current entry price ({current_price}).",
            )

        return RiskEvaluation(
            decision=RiskDecision.APPROVED,
            rule_name=self.name,
            reason="Take-profit target is valid.",
        )
