"""
BETHBot — Maximum Open Positions Rule.

Limits the maximum number of simultaneous open positions allowed across the portfolio.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.execution.base import OrderRequest, OrderSide
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState


class MaxOpenPositionsRule(BaseRiskRule):
    """
    Rejects new buy orders if the number of open positions matches or exceeds max_open_positions.
    """

    name = "max_open_positions"
    priority = 15

    def __init__(self, max_open_positions: int = 2):
        self.max_open_positions = max_open_positions

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
                reason="Sell orders reduce open positions",
            )

        # Count active open positions (quantity > 0)
        open_positions_count = sum(1 for qty in portfolio_state.positions.values() if qty > 0)

        # If adding a new position for a symbol that doesn't already have one
        existing_qty = portfolio_state.positions.get(order.asset_symbol, Decimal("0"))
        if existing_qty == 0 and open_positions_count >= self.max_open_positions:
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=(
                    f"REJECTED: Maximum open positions limit reached ({self.max_open_positions}). "
                    f"Current open positions count is {open_positions_count}."
                ),
            )

        return RiskEvaluation(
            decision=RiskDecision.APPROVED,
            rule_name=self.name,
            reason="Open positions count is within limits.",
        )
