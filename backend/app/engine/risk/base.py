"""
BETHBot — Abstract risk rule.

Every risk rule evaluates a single constraint and returns a decision.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.engine.execution.base import OrderRequest
from app.engine.strategy.base import PortfolioState


class RiskDecision(StrEnum):
    """Outcome of a risk rule evaluation."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"  # Rule can downsize the order


@dataclass
class RiskEvaluation:
    """Result of evaluating an order against a risk rule."""

    decision: RiskDecision
    rule_name: str
    reason: str
    original_quantity: Decimal | None = None
    adjusted_quantity: Decimal | None = None


class BaseRiskRule(ABC):
    """
    Abstract risk rule. Each rule evaluates one constraint.

    Rules are stateless — they receive all context through method arguments.
    """

    name: str = "unnamed_rule"
    priority: int = 0  # Lower = evaluated first

    @abstractmethod
    def evaluate(
        self,
        order: OrderRequest,
        portfolio_state: PortfolioState,
        current_price: Decimal,
    ) -> RiskEvaluation:
        """
        Evaluate the order against this rule.

        Args:
            order: The proposed order
            portfolio_state: Current portfolio state
            current_price: Current market price for the asset

        Returns:
            RiskEvaluation with APPROVED, REJECTED, or MODIFIED
        """
        ...
