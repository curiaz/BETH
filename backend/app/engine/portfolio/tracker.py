"""
BETHBot — Portfolio tracker.

Tracks portfolio state in memory during backtests and paper trading.
No database dependencies — pure logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.engine.execution.base import Fill, OrderSide
from app.engine.strategy.base import PortfolioState


@dataclass
class PortfolioTracker:
    """
    Tracks portfolio state during a trading session.

    Maintains cash balance, positions, and equity history.
    Used by backtester and paper trader.
    """

    initial_capital: Decimal = Decimal("10000")
    cash: Decimal = Decimal("10000")
    positions: dict[str, Decimal] = field(default_factory=dict)  # symbol → quantity
    avg_entry_prices: dict[str, Decimal] = field(default_factory=dict)  # symbol → avg price
    realized_pnl: Decimal = Decimal("0")
    total_fees: Decimal = Decimal("0")
    peak_equity: Decimal = Decimal("10000")
    daily_start_equity: Decimal = Decimal("10000")
    current_prices: dict[str, Decimal] = field(default_factory=dict)  # symbol → price

    # History for equity curve
    equity_history: list[tuple[datetime, float]] = field(default_factory=list)
    trade_count: int = 0

    def reset(self, initial_capital: Decimal) -> None:
        """Reset tracker for a new session."""
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions.clear()
        self.avg_entry_prices.clear()
        self.realized_pnl = Decimal("0")
        self.total_fees = Decimal("0")
        self.peak_equity = initial_capital
        self.daily_start_equity = initial_capital
        self.current_prices.clear()
        self.equity_history.clear()
        self.trade_count = 0

    def update_price(self, symbol: str, price: Decimal) -> None:
        """Update the current market price for a symbol."""
        self.current_prices[symbol] = price

    def process_fill(self, fill: Fill) -> None:
        """
        Update portfolio state based on a trade fill.

        Handles:
          - Cash deduction/addition
          - Position quantity update
          - Average entry price calculation
          - Realized PnL on closes
          - Fee tracking
        """
        self.trade_count += 1
        self.total_fees += fill.fee

        current_qty = self.positions.get(fill.asset_symbol, Decimal("0"))

        if fill.side == OrderSide.BUY:
            # Buying: deduct cash, increase position
            cost = fill.price * fill.quantity + fill.fee
            self.cash -= cost

            # Update average entry price
            if current_qty > 0:
                old_cost = self.avg_entry_prices.get(fill.asset_symbol, Decimal("0")) * current_qty
                new_cost = fill.price * fill.quantity
                total_qty = current_qty + fill.quantity
                self.avg_entry_prices[fill.asset_symbol] = (
                    (old_cost + new_cost) / total_qty if total_qty > 0 else fill.price
                )
            else:
                self.avg_entry_prices[fill.asset_symbol] = fill.price

            self.positions[fill.asset_symbol] = current_qty + fill.quantity

        elif fill.side == OrderSide.SELL:
            # Selling: add cash, decrease position
            revenue = fill.price * fill.quantity - fill.fee
            self.cash += revenue

            # Calculate realized PnL
            entry_price = self.avg_entry_prices.get(fill.asset_symbol, fill.price)
            pnl = (fill.price - entry_price) * fill.quantity - fill.fee
            self.realized_pnl += pnl

            new_qty = current_qty - fill.quantity
            if new_qty <= 0:
                # Position closed
                self.positions.pop(fill.asset_symbol, None)
                self.avg_entry_prices.pop(fill.asset_symbol, None)
            else:
                self.positions[fill.asset_symbol] = new_qty

        # Update current price
        self.current_prices[fill.asset_symbol] = fill.price

    @property
    def unrealized_pnl(self) -> Decimal:
        """Calculate total unrealized PnL across all open positions."""
        pnl = Decimal("0")
        for symbol, qty in self.positions.items():
            if qty > 0 and symbol in self.current_prices and symbol in self.avg_entry_prices:
                pnl += (self.current_prices[symbol] - self.avg_entry_prices[symbol]) * qty
        return pnl

    @property
    def total_equity(self) -> Decimal:
        """Total portfolio value = cash + unrealized position value."""
        position_value = Decimal("0")
        for symbol, qty in self.positions.items():
            price = self.current_prices.get(symbol, self.avg_entry_prices.get(symbol, Decimal("0")))
            position_value += qty * price
        return self.cash + position_value

    @property
    def daily_pnl(self) -> Decimal:
        """PnL since the start of the current day."""
        return self.total_equity - self.daily_start_equity

    def record_equity(self, timestamp: datetime) -> None:
        """Record current equity for the equity curve."""
        equity = float(self.total_equity)
        self.equity_history.append((timestamp, equity))

        # Update peak equity
        equity_dec = self.total_equity
        if equity_dec > self.peak_equity:
            self.peak_equity = equity_dec

    def start_new_day(self) -> None:
        """Mark the start of a new trading day."""
        self.daily_start_equity = self.total_equity

    def get_portfolio_state(self) -> PortfolioState:
        """Get a snapshot of the current portfolio state for strategies."""
        return PortfolioState(
            total_equity=self.total_equity,
            cash_balance=self.cash,
            peak_equity=self.peak_equity,
            positions=dict(self.positions),
            unrealized_pnl=self.unrealized_pnl,
            realized_pnl=self.realized_pnl,
            daily_pnl=self.daily_pnl,
        )
