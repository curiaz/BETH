"""
BETHBot — Live execution handler (STUB).

Phase 1: This handler raises NotImplementedError for ALL operations.
Live trading is disabled until explicitly approved and tested via sandbox.
"""

from __future__ import annotations

from app.core.exceptions import LiveTradingDisabledError
from app.engine.execution.base import (
    BaseExecutionHandler,
    Fill,
    OrderRequest,
    OrderStatus,
)


class LiveExecutor(BaseExecutionHandler):
    """
    Live trading execution handler — DISABLED in Phase 1.

    All methods raise LiveTradingDisabledError.
    This stub exists so the code compiles and the execution handler
    pattern is complete, but it cannot be used.
    """

    async def submit_order(self, order: OrderRequest) -> Fill:
        raise LiveTradingDisabledError()

    async def cancel_order(self, order_id: str) -> bool:
        raise LiveTradingDisabledError()

    async def get_order_status(self, order_id: str) -> OrderStatus:
        raise LiveTradingDisabledError()
