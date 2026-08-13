"""
BETHBot — Risk manager.

Orchestrates a pipeline of risk rules. Every order must pass all rules.
"""

from __future__ import annotations

from decimal import Decimal

from app.core.logging import get_logger
from app.engine.execution.base import OrderRequest
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.strategy.base import PortfolioState

logger = get_logger(__name__)


class RiskManager:
    """
    Orchestrates risk evaluation pipeline.

    Rules are sorted by priority (lower = first) and evaluated sequentially.
    All rules are evaluated for complete diagnostics, even if one rejects.
    """

    def __init__(self, rules: list[BaseRiskRule] | None = None):
        self._rules = sorted(rules or [], key=lambda r: r.priority)

    def add_rule(self, rule: BaseRiskRule) -> None:
        """Add a rule to the pipeline."""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)

    def remove_rule(self, rule_name: str) -> None:
        """Remove a rule by name."""
        self._rules = [r for r in self._rules if r.name != rule_name]

    def evaluate(
        self,
        order: OrderRequest,
        portfolio_state: PortfolioState,
        current_price: Decimal,
    ) -> list[RiskEvaluation]:
        """
        Run all rules against the order.

        Returns a list of evaluations. Check is_approved() on the result
        to determine if the order should proceed.
        """
        evaluations: list[RiskEvaluation] = []

        for rule in self._rules:
            try:
                evaluation = rule.evaluate(order, portfolio_state, current_price)
                evaluations.append(evaluation)

                if evaluation.decision == RiskDecision.REJECTED:
                    logger.warning(
                        "risk.rejected",
                        rule=rule.name,
                        reason=evaluation.reason,
                        order_id=order.id,
                        symbol=order.asset_symbol,
                    )
                elif evaluation.decision == RiskDecision.MODIFIED:
                    logger.info(
                        "risk.modified",
                        rule=rule.name,
                        reason=evaluation.reason,
                        original_qty=str(evaluation.original_quantity),
                        adjusted_qty=str(evaluation.adjusted_quantity),
                    )
            except Exception as e:
                # A failing rule rejects the order for safety
                logger.error("risk.rule_error", rule=rule.name, error=str(e))
                evaluations.append(
                    RiskEvaluation(
                        decision=RiskDecision.REJECTED,
                        rule_name=rule.name,
                        reason=f"Rule evaluation error: {e}",
                    )
                )

        return evaluations

    @staticmethod
    def is_approved(evaluations: list[RiskEvaluation]) -> bool:
        """Check if all rules approved the order."""
        return all(e.decision != RiskDecision.REJECTED for e in evaluations)

    @staticmethod
    def get_rejections(evaluations: list[RiskEvaluation]) -> list[RiskEvaluation]:
        """Get only the rejection evaluations."""
        return [e for e in evaluations if e.decision == RiskDecision.REJECTED]

    @property
    def rules(self) -> list[BaseRiskRule]:
        """Return the current rules in priority order."""
        return list(self._rules)
