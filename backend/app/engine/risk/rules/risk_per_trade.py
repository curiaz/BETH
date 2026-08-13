"""
BETHBot — Maximum Risk Per Trade Rule.

Limits the maximum dollar or percentage loss per trade based on the stop-loss distance.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.execution.base import OrderRequest, OrderSide
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState


class MaxRiskPerTradeRule(BaseRiskRule):
    """
    Rejects order if the maximum potential loss (quantity * (entry_price - stop_loss))
    exceeds max_risk_pct of portfolio total equity.
    """

    name = "max_risk_per_trade"
    priority = 25

    def __init__(self, max_risk_pct: float = 0.02):
        self.max_risk_pct = max_risk_pct

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
                reason="Sell orders do not increase risk per trade",
            )

        total_equity = portfolio_state.total_equity
        if total_equity <= 0:
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason="REJECTED: Portfolio equity is zero or negative.",
            )

        max_allowed_risk = total_equity * Decimal(str(self.max_risk_pct))

        # Check if stop-loss is set in order or metadata
        stop_loss = getattr(order, "stop_loss", None)
        if stop_loss is None:
            # Assume fallback 5% stop-loss if not explicitly set
            risk_per_unit = current_price * Decimal("0.05")
        else:
            risk_per_unit = abs(current_price - Decimal(str(stop_loss)))

        potential_loss = order.quantity * risk_per_unit

        if potential_loss > max_allowed_risk:
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=(
                    f"REJECTED: Maximum risk per trade exceeded. "
                    f"Potential loss ({potential_loss:.2f}) exceeds allowed limit ({max_allowed_risk:.2f})."
                ),
                original_quantity=order.quantity,
            )

        return RiskEvaluation(
            decision=RiskDecision.APPROVED,
            rule_name=self.name,
            reason="Risk per trade is within acceptable limits.",
        )
