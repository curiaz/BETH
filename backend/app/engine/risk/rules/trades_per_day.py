"""
BETHBot — Maximum Trades Per Day Rule.

Limits the maximum number of executed trades allowed per day.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.execution.base import OrderRequest
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState


class MaxTradesPerDayRule(BaseRiskRule):
    """
    Rejects orders if the number of trades executed today matches or exceeds max_trades_per_day.
    """

    name = "max_trades_per_day"
    priority = 16

    def __init__(self, max_trades_per_day: int = 10):
        self.max_trades_per_day = max_trades_per_day
        self._today_trade_count: int = 0

    def set_today_trade_count(self, count: int) -> None:
        self._today_trade_count = count

    def increment_trade_count(self) -> None:
        self._today_trade_count += 1

    def reset_daily(self) -> None:
        self._today_trade_count = 0

    def evaluate(
        self,
        order: OrderRequest,
        portfolio_state: PortfolioState,
        current_price: Decimal,
    ) -> RiskEvaluation:
        if self._today_trade_count >= self.max_trades_per_day:
            return RiskEvaluation(
                decision=RiskDecision.REJECTED,
                rule_name=self.name,
                reason=(
                    f"REJECTED: Maximum trades per day limit reached ({self.max_trades_per_day}). "
                    f"Executed trades today: {self._today_trade_count}."
                ),
            )

        return RiskEvaluation(
            decision=RiskDecision.APPROVED,
            rule_name=self.name,
            reason="Daily trade count is within limit.",
        )
