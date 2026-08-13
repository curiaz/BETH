"""
BETHBot — Stop-Loss Validation Rule.

Validates that proposed orders include a valid stop-loss or respect maximum stop-loss distance.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.execution.base import OrderRequest, OrderSide
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState


class StopLossRule(BaseRiskRule):
    """
    Validates stop-loss placement for buy orders.
    """

    name = "stop_loss_validation"
    priority = 20

    def __init__(self, max_stop_loss_pct: float = 0.10, require_stop_loss: bool = False):
        self.max_stop_loss_pct = max_stop_loss_pct
        self.require_stop_loss = require_stop_loss

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
                reason="Sell orders do not require stop-loss validation",
            )

        stop_loss = getattr(order, "stop_loss", None)

        if stop_loss is None:
            if self.require_stop_loss:
                return RiskEvaluation(
                    decision=RiskDecision.REJECTED,
                    rule_name=self.name,
                    reason="REJECTED: Stop-loss is required for buy orders.",
                )
            return RiskEvaluation(
                decision=RiskDecision.APPROVED,
                rule_name=self.name,
                reason="No explicit stop-loss provided; passing validation.",
            )

        stop_price = Decimal(str(stop_loss))
        if stop_price >= current_price:
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=f"REJECTED: Stop-loss price ({stop_price}) must be below current entry price ({current_price}).",
            )

        distance_pct = float((current_price - stop_price) / current_price)
        if distance_pct > self.max_stop_loss_pct:
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=(
                    f"REJECTED: Stop-loss distance ({distance_pct * 100:.1f}%) exceeds "
                    f"maximum allowed limit ({self.max_stop_loss_pct * 100:.1f}%)."
                ),
            )

        return RiskEvaluation(
            decision=RiskDecision.APPROVED,
            rule_name=self.name,
            reason="Stop-loss price is valid.",
        )
