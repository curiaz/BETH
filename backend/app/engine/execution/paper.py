"""
BETHBot — Paper trading execution handler.

Simulates fills against live market prices without real money.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.engine.execution.base import (
    BaseExecutionHandler,
    Fill,
    OrderRequest,
    OrderSide,
    OrderStatus,
)


class PaperExecutor(BaseExecutionHandler):
    """
    Simulates fills against live market prices.

    - Fills at the provided market price with simulated slippage
    - Tracks a virtual order book
    - Logs all activity for audit
    """

    def __init__(
        self,
        slippage_pct: Decimal = Decimal("0.0005"),
        fee_pct: Decimal = Decimal("0.001"),
    ):
        self.slippage_pct = slippage_pct
        self.fee_pct = fee_pct
        self._current_price: dict[str, Decimal] = {}  # symbol → price
        self._orders: dict[str, OrderStatus] = {}

    def update_price(self, symbol: str, price: Decimal) -> None:
        """Update the current market price for a symbol."""
        self._current_price[symbol] = price

    async def submit_order(self, order: OrderRequest) -> Fill:
        """
        Simulate a fill at the current market price.

        Requires that update_price() has been called for the order's symbol.
        """
        if order.asset_symbol not in self._current_price:
            raise RuntimeError(
                f"PaperExecutor: no price available for {order.asset_symbol}. "
                f"Call update_price() first."
            )

        base_price = self._current_price[order.asset_symbol]

        # Apply slippage
        slippage_amount = base_price * self.slippage_pct
        if order.side == OrderSide.BUY:
            fill_price = base_price + slippage_amount
        else:
            fill_price = base_price - slippage_amount

        # Calculate fee
        fee = fill_price * order.quantity * self.fee_pct

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
            timestamp=datetime.now(timezone.utc),
            status=OrderStatus.FILLED,
        )

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        if order_id in self._orders and self._orders[order_id] == OrderStatus.PENDING:
            self._orders[order_id] = OrderStatus.CANCELLED
            return True
        return False

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Get the status of a tracked order."""
        return self._orders.get(order_id, OrderStatus.PENDING)
