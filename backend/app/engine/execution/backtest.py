"""
BETHBot — Backtest execution handler.

Simulates order fills against historical data with configurable
slippage and fee models. Avoids look-ahead bias.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pandas as pd

from app.engine.execution.base import (
    BaseExecutionHandler,
    Fill,
    OrderRequest,
    OrderSide,
    OrderStatus,
)


class BacktestExecutor(BaseExecutionHandler):
    """
    Simulates order fills against historical data.

    Features:
      - Configurable slippage model (percentage-based)
      - Configurable fee model (from asset or override)
      - Fills at current bar's close price (standard backtest approach)
      - Partial fills not simulated in Phase 1
    """

    def __init__(
        self,
        slippage_pct: Decimal = Decimal("0.001"),
        fee_pct: Decimal = Decimal("0.001"),
    ):
        self.slippage_pct = slippage_pct
        self.fee_pct = fee_pct
        self._current_bar: pd.Series | None = None
        self._orders: dict[str, OrderStatus] = {}

    def set_current_bar(self, bar: pd.Series) -> None:
        """Called by the backtester to update the current market context."""
        self._current_bar = bar

    async def submit_order(self, order: OrderRequest) -> Fill:
        """
        Simulate a fill at the current bar's close price.

        Applies slippage:
          - BUY orders fill at close + slippage (worse for buyer)
          - SELL orders fill at close - slippage (worse for seller)
        """
        if self._current_bar is None:
            raise RuntimeError("BacktestExecutor: no current bar set. Call set_current_bar first.")

        base_price = Decimal(str(self._current_bar["close"]))

        # Apply slippage
        slippage_amount = base_price * self.slippage_pct
        if order.side == OrderSide.BUY:
            fill_price = base_price + slippage_amount
        else:
            fill_price = base_price - slippage_amount

        # Calculate fee
        fee = fill_price * order.quantity * self.fee_pct

        # Determine timestamp
        bar_time = self._current_bar.name
        if isinstance(bar_time, pd.Timestamp):
            timestamp = bar_time.to_pydatetime()
        elif isinstance(bar_time, datetime):
            timestamp = bar_time
        else:
            timestamp = datetime.now(timezone.utc)

        # Track order
        self._orders[order.id] = OrderStatus.FILLED

        return Fill(
            order_id=order.id,
            asset_symbol=order.asset_symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            fee=fee,
            slippage=slippage_amount,
            timestamp=timestamp,
            status=OrderStatus.FILLED,
        )

    async def cancel_order(self, order_id: str) -> bool:
        """In backtesting, orders are instantly filled so cancellation is a no-op."""
        if order_id in self._orders:
            self._orders[order_id] = OrderStatus.CANCELLED
            return True
        return False

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Get the status of a tracked order."""
        return self._orders.get(order_id, OrderStatus.PENDING)

    def reset(self) -> None:
        """Reset state for a new backtest run."""
        self._current_bar = None
        self._orders.clear()
