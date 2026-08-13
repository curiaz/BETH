"""
BETHBot — Quantara Paper Broker Engine.

Simulates account balance, BUY/SELL market order fills, fees, slippage,
positions, and trade history in PAPER mode with high precision Decimals.

STRICT INVARIANT: PaperBroker NEVER communicates with any external exchange API.
Execution flow: Strategy → RiskManager → PaperBroker → Portfolio → Database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.core.logging import get_logger
from app.core.market_config import market_registry
from app.engine.execution.base import (
    BaseExecutionHandler,
    Fill,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
)

logger = get_logger(__name__)


class PaperBroker(BaseExecutionHandler):
    """
    Quantara Paper Trading Broker.

    Simulates paper trading order execution, position tracking, account balance management,
    fees, slippage, duplicate order protection, and balance/position validations.
    """

    def __init__(
        self,
        initial_balance: Decimal = Decimal("10000.0"),
        slippage_pct: Decimal = Decimal("0.0005"),
        fee_pct: Decimal = Decimal("0.001"),
    ):
        self.initial_balance: Decimal = initial_balance
        self.cash_balance: Decimal = initial_balance
        self.slippage_pct: Decimal = slippage_pct
        self.fee_pct: Decimal = fee_pct

        self._current_prices: dict[str, Decimal] = {}
        self._positions: dict[str, Decimal] = {}
        self._orders: dict[str, OrderStatus] = {}
        self._trade_history: list[dict[str, Any]] = []

    def reset(self, initial_balance: Decimal | None = None) -> None:
        """Reset PaperBroker state."""
        bal = initial_balance if initial_balance is not None else self.initial_balance
        self.initial_balance = bal
        self.cash_balance = bal
        self._current_prices.clear()
        self._positions.clear()
        self._orders.clear()
        self._trade_history.clear()

    def update_price(self, symbol: str, price: Decimal) -> None:
        """Update current market price for a symbol."""
        norm_symbol = market_registry.validate_symbol(symbol)
        if price <= 0:
            raise ValueError(f"Market price for {norm_symbol} must be positive (> 0)")
        self._current_prices[norm_symbol] = price

    def update_prices(self, price_map: dict[str, Decimal]) -> None:
        """Update current market prices for multiple symbols."""
        for sym, p in price_map.items():
            self.update_price(sym, p)

    async def submit_order(self, order: OrderRequest) -> Fill:
        """
        Submit a paper trading order for execution against simulated market prices.
        """
        # 1. Duplicate order protection
        if order.id in self._orders:
            raise ValueError(f"Duplicate order ID '{order.id}' already processed")

        # 2. Symbol format and asset validation
        norm_symbol = market_registry.validate_symbol(order.asset_symbol)

        # 3. Invalid quantity validation
        if order.quantity <= 0:
            self._orders[order.id] = OrderStatus.REJECTED
            raise ValueError(f"Invalid order quantity '{order.quantity}'. Quantity must be positive (> 0).")

        # 4. Market price check
        if norm_symbol not in self._current_prices:
            self._orders[order.id] = OrderStatus.REJECTED
            raise ValueError(f"PaperBroker: No market price available for {norm_symbol}. Call update_price() first.")

        base_price = self._current_prices[norm_symbol]

        # 5. Apply slippage
        slippage_amount = base_price * self.slippage_pct
        if order.side == OrderSide.BUY:
            fill_price = base_price + slippage_amount
        else:
            fill_price = base_price - slippage_amount

        # 6. Calculate fee
        fee = fill_price * order.quantity * self.fee_pct

        # 7. Insufficient Balance / Position validation
        current_pos = self._positions.get(norm_symbol, Decimal("0"))

        if order.side == OrderSide.BUY:
            required_cost = (fill_price * order.quantity) + fee
            if self.cash_balance < required_cost:
                self._orders[order.id] = OrderStatus.REJECTED
                raise ValueError(
                    f"REJECTED: Insufficient balance ({self.cash_balance:.2f} USDT) "
                    f"for required order cost ({required_cost:.2f} USDT)."
                )

            # Deduct cash and update position
            self.cash_balance -= required_cost
            self._positions[norm_symbol] = current_pos + order.quantity

        elif order.side == OrderSide.SELL:
            if current_pos < order.quantity:
                self._orders[order.id] = OrderStatus.REJECTED
                raise ValueError(
                    f"REJECTED: Insufficient position ({current_pos} {norm_symbol}) "
                    f"for sell order ({order.quantity})."
                )

            # Add net revenue and reduce position
            net_revenue = (fill_price * order.quantity) - fee
            self.cash_balance += net_revenue

            new_pos = current_pos - order.quantity
            if new_pos <= 0:
                self._positions.pop(norm_symbol, None)
            else:
                self._positions[norm_symbol] = new_pos

        # 8. Record order status and build Fill
        self._orders[order.id] = OrderStatus.FILLED
        timestamp = datetime.now(timezone.utc)

        fill = Fill(
            order_id=order.id,
            asset_symbol=norm_symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            fee=fee,
            slippage=slippage_amount,
            timestamp=timestamp,
            status=OrderStatus.FILLED,
        )

        # 9. Record in trade history
        self._trade_history.append({
            "order_id": order.id,
            "timestamp": timestamp.isoformat(),
            "symbol": norm_symbol,
            "side": order.side.value,
            "quantity": float(order.quantity),
            "price": float(fill_price),
            "fee": float(fee),
            "slippage": float(slippage_amount),
            "cash_balance": float(self.cash_balance),
        })

        logger.info(
            "paper_broker.order_filled",
            order_id=order.id,
            symbol=norm_symbol,
            side=order.side.value,
            quantity=str(order.quantity),
            fill_price=str(fill_price),
            remaining_cash=str(self.cash_balance),
        )

        return fill

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        if order_id in self._orders and self._orders[order_id] == OrderStatus.PENDING:
            self._orders[order_id] = OrderStatus.CANCELLED
            return True
        return False

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Query status of a tracked order."""
        return self._orders.get(order_id, OrderStatus.PENDING)

    def get_account_balance(self) -> Decimal:
        """Get current virtual USDT cash balance."""
        return self.cash_balance

    def get_position(self, symbol: str) -> Decimal:
        """Get position quantity for a specific asset symbol."""
        norm_symbol = market_registry.validate_symbol(symbol)
        return self._positions.get(norm_symbol, Decimal("0"))

    def get_positions(self) -> dict[str, Decimal]:
        """Get copy of all active open positions."""
        return dict(self._positions)

    def get_trade_history(self) -> list[dict[str, Any]]:
        """Get complete paper trading trade log history."""
        return list(self._trade_history)


# Alias for backward compatibility
PaperExecutor = PaperBroker
