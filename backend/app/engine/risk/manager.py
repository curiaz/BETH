"""
BETHBot — Risk Manager Engine.

Evaluates every proposed trade order before execution against a configurable pipeline
of risk rules (position size, portfolio exposure, risk per trade, stop-loss, take-profit,
daily loss, max open positions, max trades per day).

Returns a structured decision (APPROVED or REJECTED) with human-readable rejection reasons.

STRICT INVARIANT: The RiskManager NEVER executes orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from app.core.logging import get_logger
from app.engine.execution.base import OrderRequest
from app.engine.risk.base import BaseRiskRule, RiskDecision, RiskEvaluation
from app.engine.risk.rules.daily_loss import DailyLossRule
from app.engine.risk.rules.exposure import ExposureRule
from app.engine.risk.rules.max_drawdown import MaxDrawdownRule
from app.engine.risk.rules.open_positions import MaxOpenPositionsRule
from app.engine.risk.rules.position_size import PositionSizeRule
from app.engine.risk.rules.risk_per_trade import MaxRiskPerTradeRule
from app.engine.risk.rules.stop_loss import StopLossRule
from app.engine.risk.rules.take_profit import TakeProfitRule
from app.engine.risk.rules.trades_per_day import MaxTradesPerDayRule
from app.engine.strategy.base import PortfolioState

logger = get_logger(__name__)


@dataclass
class RiskResult:
    """
    Structured outcome of a proposed trade evaluation.
    """

    decision: RiskDecision  # APPROVED or REJECTED
    reason: str  # Human-readable explanation
    evaluations: list[RiskEvaluation]

    @property
    def is_approved(self) -> bool:
        return self.decision == RiskDecision.APPROVED


class RiskManager:
    """
    Orchestrates the Risk Management Engine.

    Evaluates proposed trade orders against priority-ordered risk rules.
    Does NOT execute orders under any circumstances.
    """

    def __init__(self, rules: Sequence[BaseRiskRule] | None = None):
        self._rules = sorted(list(rules or []), key=lambda r: r.priority)

    @classmethod
    def create_default(
        cls,
        max_position_size_pct: float = 0.20,
        max_portfolio_exposure_pct: float = 0.80,
        max_risk_per_trade_pct: float = 0.02,
        max_stop_loss_pct: float = 0.10,
        require_stop_loss: bool = False,
        max_daily_loss_pct: float = 0.03,
        max_drawdown_pct: float = 0.15,
        max_open_positions: int = 2,
        max_trades_per_day: int = 10,
    ) -> RiskManager:
        """
        Factory method to construct a standard RiskManager with all 8 core rules configured.
        """
        rules = [
            PositionSizeRule(max_position_size_pct),
            ExposureRule(max_portfolio_exposure_pct),
            MaxRiskPerTradeRule(max_risk_per_trade_pct),
            StopLossRule(max_stop_loss_pct, require_stop_loss=require_stop_loss),
            TakeProfitRule(),
            DailyLossRule(max_daily_loss_pct),
            MaxDrawdownRule(max_drawdown_pct),
            MaxOpenPositionsRule(max_open_positions),
            MaxTradesPerDayRule(max_trades_per_day),
        ]
        return cls(rules)

    def add_rule(self, rule: BaseRiskRule) -> None:
        """Add a rule to the pipeline."""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)

    def evaluate_order(
        self,
        order: OrderRequest,
        portfolio_state: PortfolioState,
        current_price: Decimal,
    ) -> RiskResult:
        """
        Evaluate a proposed trade order against all configured risk rules.

        Returns:
            Structured RiskResult with decision (APPROVED / REJECTED) and reason.
        """
        evaluations: list[RiskEvaluation] = []
        rejection_reasons: list[str] = []

        for rule in self._rules:
            try:
                eval_res = rule.evaluate(order, portfolio_state, current_price)
                evaluations.append(eval_res)

                if eval_res.decision == RiskDecision.REJECTED:
                    rejection_reasons.append(eval_res.reason)
                    logger.warning(
                        "risk_manager.rejected",
                        rule=rule.name,
                        reason=eval_res.reason,
                        symbol=order.asset_symbol,
                    )
            except Exception as e:
                err_msg = f"REJECTED: Risk rule '{rule.name}' failure: {e}"
                logger.error("risk_manager.rule_error", rule=rule.name, error=str(e))
                evaluations.append(
                    RiskEvaluation(
                        decision=RiskDecision.REJECTED,
                        rule_name=rule.name,
                        reason=err_msg,
                    )
                )
                rejection_reasons.append(err_msg)

        if rejection_reasons:
            primary_reason = rejection_reasons[0]
            return RiskResult(
                decision=RiskDecision.REJECTED,
                reason=primary_reason,
                evaluations=evaluations,
            )

        return RiskResult(
            decision=RiskDecision.APPROVED,
            reason="APPROVED",
            evaluations=evaluations,
        )

    def evaluate(
        self,
        order: OrderRequest,
        portfolio_state: PortfolioState,
        current_price: Decimal,
    ) -> list[RiskEvaluation]:
        """Backward-compatible evaluation method returning list of RiskEvaluations."""
        result = self.evaluate_order(order, portfolio_state, current_price)
        return result.evaluations

    @staticmethod
    def is_approved(evaluations: list[RiskEvaluation]) -> bool:
        """Check if all rules approved the order."""
        return all(e.decision != RiskDecision.REJECTED for e in evaluations)

    @staticmethod
    def get_rejections(evaluations: list[RiskEvaluation]) -> list[RiskEvaluation]:
        """Get only rejection evaluations."""
        return [e for e in evaluations if e.decision == RiskDecision.REJECTED]

    @property
    def rules(self) -> list[BaseRiskRule]:
        return list(self._rules)
