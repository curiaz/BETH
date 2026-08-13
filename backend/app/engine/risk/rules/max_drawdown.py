"""
BETHBot — Max drawdown risk rule.

Halts all trading if portfolio drawdown exceeds threshold.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.execution.base import OrderRequest
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState


class MaxDrawdownRule(BaseRiskRule):
    """
    Halts all trading if drawdown from peak equity exceeds threshold.
    Default: Stop trading at 15% drawdown.
    """

    name = "max_drawdown"
    priority = 0  # Highest priority — checked first

    def __init__(self, max_drawdown_pct: float = 0.15):
        self.max_drawdown_pct = max_drawdown_pct

    def evaluate(
        self,
        order: OrderRequest,
        portfolio_state: PortfolioState,
        current_price: Decimal,
    ) -> RiskEvaluation:
        if portfolio_state.peak_equity <= 0:
            return RiskEvaluation(
                decision=RiskDecision.APPROVED,
                rule_name=self.name,
                reason="No peak equity recorded yet",
            )

        drawdown = (
            (portfolio_state.peak_equity - portfolio_state.total_equity)
            / portfolio_state.peak_equity
        )

        if drawdown >= Decimal(str(self.max_drawdown_pct)):
            pct = float(drawdown) * 100
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=(
                    f"Current drawdown {pct:.1f}% exceeds max "
                    f"{self.max_drawdown_pct * 100:.0f}%. All trading halted."
                ),
            )

        return RiskEvaluation(
            decision=RiskDecision.APPROVED,
            rule_name=self.name,
            reason="Drawdown within limits",
        )
