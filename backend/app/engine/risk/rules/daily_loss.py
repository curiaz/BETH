"""
BETHBot — Daily loss limit risk rule.

Stops trading for the day if daily losses exceed threshold.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.execution.base import OrderRequest
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState


class DailyLossRule(BaseRiskRule):
    """
    Stops trading for the current day if daily PnL losses exceed threshold.
    Default: Max 3% daily loss.
    """

    name = "daily_loss"
    priority = 1

    def __init__(self, max_daily_loss_pct: float = 0.03):
        self.max_daily_loss_pct = max_daily_loss_pct

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

        # daily_pnl is negative when losing
        daily_loss = portfolio_state.daily_pnl
        max_loss = portfolio_state.total_equity * Decimal(str(self.max_daily_loss_pct))

        # daily_pnl < 0 means loss; check if loss exceeds limit
        if daily_loss < Decimal("0") and abs(daily_loss) >= max_loss:
            loss_pct = float(abs(daily_loss) / portfolio_state.total_equity) * 100
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=(
                    f"Daily loss {loss_pct:.1f}% exceeds max "
                    f"{self.max_daily_loss_pct * 100:.0f}%. Trading halted for the day."
                ),
            )

        return RiskEvaluation(
            decision=RiskDecision.APPROVED,
            rule_name=self.name,
            reason="Daily loss within limits",
        )
