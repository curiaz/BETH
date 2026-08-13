"""
BETHBot — Quantara Portfolio Engine.

Tracks multi-asset portfolio states (USDT cash, BTC/USDT position, ETH/USDT position, etc.),
average entry prices, current market prices, position values, unrealized P/L, realized P/L,
total portfolio valuation, and asset/portfolio exposure percentages.

Independent from exchange implementations — consumes Fill and price updates from any broker
(BacktestExecutor, PaperBroker, TestnetBroker).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.core.logging import get_logger
from app.core.market_config import market_registry
from app.engine.execution.base import Fill, OrderSide
from app.engine.strategy.base import PortfolioState

logger = get_logger(__name__)


# ============================================================================
# 1. Position Snapshot Dataclass
# ============================================================================


@dataclass(frozen=True)
class PositionSnapshot:
    """
    Immutable snapshot of a single asset position in the portfolio.
    """

    symbol: str
    quantity: Decimal
    avg_entry_price: Decimal
    current_price: Decimal
    position_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    exposure_pct: float  # Position value as % of total portfolio equity


# ============================================================================
# 2. Portfolio Snapshot Dataclass
# ============================================================================


@dataclass(frozen=True)
class PortfolioSnapshot:
    """
    Immutable snapshot of total portfolio valuation and multi-asset positions.
    """

    cash_usdt: Decimal
    positions: dict[str, PositionSnapshot]
    total_portfolio_value: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    total_exposure_usdt: Decimal
    total_exposure_pct: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# 3. Portfolio Engine Implementation
# ============================================================================


class PortfolioEngine:
    """
    Quantara Portfolio Engine.

    Maintains high-precision Decimal monetary accounting for multi-asset positions.
    Tracks cash balance (USDT), open positions (e.g. BTC, ETH), average entry prices,
    market values, unrealized/realized PnL, and exposure ratios.
    """

    def __init__(self, initial_cash: Decimal = Decimal("10000.0")):
        self.initial_capital: Decimal = initial_cash
        self.cash_usdt: Decimal = initial_cash

        # Multi-asset position tracking
        self.positions: dict[str, Decimal] = {}  # symbol -> quantity
        self.avg_entry_prices: dict[str, Decimal] = {}  # symbol -> avg_entry_price
        self.current_prices: dict[str, Decimal] = {}  # symbol -> current_price
        self.realized_pnl_by_symbol: dict[str, Decimal] = {}  # symbol -> cumulative realized PnL

        self.total_fees: Decimal = Decimal("0")
        self.total_realized_pnl: Decimal = Decimal("0")

    def reset(self, initial_cash: Decimal | None = None) -> None:
        """Reset portfolio engine state."""
        cap = initial_cash if initial_cash is not None else self.initial_capital
        self.initial_capital = cap
        self.cash_usdt = cap
        self.positions.clear()
        self.avg_entry_prices.clear()
        self.current_prices.clear()
        self.realized_pnl_by_symbol.clear()
        self.total_fees = Decimal("0")
        self.total_realized_pnl = Decimal("0")

    def update_price(self, symbol: str, price: Decimal) -> None:
        """
        Update market price for a symbol.
        """
        norm_symbol = market_registry.validate_symbol(symbol)
        if price <= 0:
            raise ValueError(f"Price for {norm_symbol} must be strictly positive (> 0)")
        self.current_prices[norm_symbol] = price

    def update_prices(self, price_map: dict[str, Decimal]) -> None:
        """Update market prices for multiple symbols simultaneously."""
        for sym, price in price_map.items():
            self.update_price(sym, price)

    def process_fill(self, fill: Fill) -> None:
        """
        Process a trade execution fill from a broker (PaperBroker, TestnetBroker, or BacktestExecutor).

        Updates:
          - Cash balance
          - Position quantity & average entry price
          - Realized PnL
          - Total fees paid
        """
        norm_symbol = market_registry.validate_symbol(fill.asset_symbol)
        qty = fill.quantity
        price = fill.price
        fee = fill.fee

        if qty <= 0 or price <= 0:
            raise ValueError(f"Fill quantity ({qty}) and price ({price}) must be positive")

        self.total_fees += fee
        self.current_prices[norm_symbol] = price

        current_qty = self.positions.get(norm_symbol, Decimal("0"))
        current_avg_entry = self.avg_entry_prices.get(norm_symbol, Decimal("0"))

        if fill.side == OrderSide.BUY:
            # BUY: Deduct cash (cost + fee), increase position quantity
            total_cost = (price * qty) + fee
            self.cash_usdt -= total_cost

            # Calculate weighted average entry price
            if current_qty > 0:
                existing_cost = current_avg_entry * current_qty
                new_purchase_cost = price * qty
                new_total_qty = current_qty + qty
                self.avg_entry_prices[norm_symbol] = (existing_cost + new_purchase_cost) / new_total_qty
            else:
                self.avg_entry_prices[norm_symbol] = price

            self.positions[norm_symbol] = current_qty + qty

            logger.info(
                "portfolio_engine.buy_fill_processed",
                symbol=norm_symbol,
                quantity=str(qty),
                price=str(price),
                new_qty=str(self.positions[norm_symbol]),
                new_avg_entry=str(self.avg_entry_prices[norm_symbol]),
            )

        elif fill.side == OrderSide.SELL:
            # SELL: Add cash revenue (revenue - fee), reduce position quantity
            net_revenue = (price * qty) - fee
            self.cash_usdt += net_revenue

            # Calculate realized PnL for closed quantity
            entry_price = current_avg_entry if current_avg_entry > 0 else price
            realized_pnl_trade = ((price - entry_price) * qty) - fee

            self.total_realized_pnl += realized_pnl_trade
            self.realized_pnl_by_symbol[norm_symbol] = (
                self.realized_pnl_by_symbol.get(norm_symbol, Decimal("0")) + realized_pnl_trade
            )

            new_qty = current_qty - qty
            if new_qty <= 0:
                # Position fully closed
                self.positions.pop(norm_symbol, None)
                self.avg_entry_prices.pop(norm_symbol, None)
            else:
                # Partial position close
                self.positions[norm_symbol] = new_qty

            logger.info(
                "portfolio_engine.sell_fill_processed",
                symbol=norm_symbol,
                quantity=str(qty),
                price=str(price),
                realized_pnl=str(realized_pnl_trade),
                remaining_qty=str(self.positions.get(norm_symbol, Decimal("0"))),
            )

    def get_position_value(self, symbol: str) -> Decimal:
        """Calculate market value of a position (quantity * current_price)."""
        norm_symbol = market_registry.validate_symbol(symbol)
        qty = self.positions.get(norm_symbol, Decimal("0"))
        if qty == 0:
            return Decimal("0")
        price = self.current_prices.get(norm_symbol, self.avg_entry_prices.get(norm_symbol, Decimal("0")))
        return qty * price

    def get_position_unrealized_pnl(self, symbol: str) -> Decimal:
        """Calculate unrealized PnL of a position ((current_price - avg_entry) * qty)."""
        norm_symbol = market_registry.validate_symbol(symbol)
        qty = self.positions.get(norm_symbol, Decimal("0"))
        if qty == 0:
            return Decimal("0")

        avg_entry = self.avg_entry_prices.get(norm_symbol, Decimal("0"))
        curr_price = self.current_prices.get(norm_symbol, avg_entry)
        return (curr_price - avg_entry) * qty

    @property
    def total_unrealized_pnl(self) -> Decimal:
        """Total unrealized PnL across all open positions."""
        total_pnl = Decimal("0")
        for sym in self.positions:
            total_pnl += self.get_position_unrealized_pnl(sym)
        return total_pnl

    @property
    def total_exposure_usdt(self) -> Decimal:
        """Total deployed position value in USDT across all open positions."""
        total_exp = Decimal("0")
        for sym in self.positions:
            total_exp += self.get_position_value(sym)
        return total_exp

    @property
    def total_portfolio_value(self) -> Decimal:
        """Total portfolio equity (USDT cash + total_exposure_usdt)."""
        return self.cash_usdt + self.total_exposure_usdt

    def get_position_snapshot(self, symbol: str) -> PositionSnapshot | None:
        """
        Get structured PositionSnapshot for a specific asset symbol.
        """
        norm_symbol = market_registry.validate_symbol(symbol)
        qty = self.positions.get(norm_symbol, Decimal("0"))
        if qty == 0:
            return None

        avg_entry = self.avg_entry_prices.get(norm_symbol, Decimal("0"))
        curr_price = self.current_prices.get(norm_symbol, avg_entry)
        pos_val = qty * curr_price
        unrealized = (curr_price - avg_entry) * qty
        realized = self.realized_pnl_by_symbol.get(norm_symbol, Decimal("0"))

        tot_val = self.total_portfolio_value
        exp_pct = float((pos_val / tot_val) * Decimal("100.0")) if tot_val > 0 else 0.0

        return PositionSnapshot(
            symbol=norm_symbol,
            quantity=qty,
            avg_entry_price=avg_entry,
            current_price=curr_price,
            position_value=pos_val,
            unrealized_pnl=unrealized,
            realized_pnl=realized,
            exposure_pct=exp_pct,
        )

    def get_snapshot(self) -> PortfolioSnapshot:
        """
        Get complete PortfolioSnapshot including cash, open positions, and total exposure.
        """
        snapshots: dict[str, PositionSnapshot] = {}
        for sym in list(self.positions.keys()):
            snap = self.get_position_snapshot(sym)
            if snap is not None:
                snapshots[sym] = snap

        tot_val = self.total_portfolio_value
        tot_exp_usdt = self.total_exposure_usdt
        tot_exp_pct = float((tot_exp_usdt / tot_val) * Decimal("100.0")) if tot_val > 0 else 0.0

        return PortfolioSnapshot(
            cash_usdt=self.cash_usdt,
            positions=snapshots,
            total_portfolio_value=tot_val,
            total_unrealized_pnl=self.total_unrealized_pnl,
            total_realized_pnl=self.total_realized_pnl,
            total_exposure_usdt=tot_exp_usdt,
            total_exposure_pct=tot_exp_pct,
            timestamp=datetime.now(timezone.utc),
        )

    def get_portfolio_state(self) -> PortfolioState:
        """
        Adapter method returning PortfolioState for strategy and risk manager consumption.
        """
        return PortfolioState(
            total_equity=self.total_portfolio_value,
            cash_balance=self.cash_usdt,
            peak_equity=self.total_portfolio_value,
            positions=dict(self.positions),
            unrealized_pnl=self.total_unrealized_pnl,
            realized_pnl=self.total_realized_pnl,
            daily_pnl=self.total_unrealized_pnl + self.total_realized_pnl,
        )
