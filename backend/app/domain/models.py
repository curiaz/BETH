"""
BETHBot — Core Domain Models.

10 Core Pydantic domain models with strict validation rules and Decimal precision:
1. Asset (e.g., BTC, ETH, USDT)
2. Market (e.g., BTC/USDT, ETH/USDT)
3. Candle (OHLCV candlestick bar)
4. Ticker (Real-time price snapshot)
5. Signal (Strategy output signal)
6. Order (Order intent & lifecycle)
7. Trade (Executed fill)
8. Position (Open/closed trading position)
9. Portfolio (Portfolio state & valuation)
10. Account (User/system trading account)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Self
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.enums import (
    AssetType,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSide,
    PositionStatus,
    Signal,
)

# Regex for asset symbol (e.g., BTC, ETH, USDT)
ASSET_CODE_REGEX = re.compile(r"^[A-Z0-9]{2,10}$")

# Regex for trading pair market symbol (e.g., BTC/USDT, ETH/USDT)
MARKET_SYMBOL_REGEX = re.compile(r"^[A-Z0-9]{2,10}/[A-Z0-9]{2,10}$")


# ============================================================================
# 1. Asset Model
# ============================================================================


class Asset(BaseModel):
    """
    Represents a currency or crypto asset (e.g., BTC, ETH, USDT).
    Assets are configurable — no hardcoding.
    """

    code: str = Field(description="Asset ticker code, e.g. BTC, ETH, USDT")
    name: str = Field(description="Full asset name, e.g. Bitcoin, Ethereum")
    precision: int = Field(default=8, ge=0, le=18, description="Decimal places for precision")
    asset_type: AssetType = Field(default=AssetType.SPOT, description="Asset classification")

    @field_validator("code")
    @classmethod
    def validate_asset_code(cls, v: str) -> str:
        code = v.strip().upper()
        if not ASSET_CODE_REGEX.match(code):
            raise ValueError(
                f"Invalid asset code '{v}'. Must be 2-10 uppercase alphanumeric characters."
            )
        return code

    model_config = {"frozen": True}


# ============================================================================
# 2. Market Model
# ============================================================================


class Market(BaseModel):
    """
    Represents a tradable market / currency pair (e.g., BTC/USDT).
    """

    symbol: str = Field(description="Trading pair symbol, e.g. BTC/USDT")
    base_asset: str = Field(description="Base asset code, e.g. BTC")
    quote_asset: str = Field(description="Quote asset code, e.g. USDT")
    exchange: str = Field(default="binance", description="Exchange name")
    asset_type: AssetType = Field(default=AssetType.SPOT)

    # Precision and limits
    tick_size: Decimal = Field(default=Decimal("0.01"), description="Price precision increment")
    lot_size: Decimal = Field(default=Decimal("0.00001"), description="Quantity precision increment")
    min_notional: Decimal = Field(
        default=Decimal("10.0"), description="Minimum order value in quote currency"
    )

    # Fees
    maker_fee: Decimal = Field(default=Decimal("0.001"), description="Maker fee rate")
    taker_fee: Decimal = Field(default=Decimal("0.001"), description="Taker fee rate")

    is_active: bool = Field(default=True, description="Whether trading is active for this market")

    @field_validator("symbol")
    @classmethod
    def validate_market_symbol(cls, v: str) -> str:
        symbol = v.strip().upper()
        if not MARKET_SYMBOL_REGEX.match(symbol):
            raise ValueError(
                f"Invalid market symbol '{v}'. Must match 'BASE/QUOTE' format (e.g. BTC/USDT)."
            )
        return symbol

    @field_validator("tick_size", "lot_size", "min_notional")
    @classmethod
    def validate_positive_decimal(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Value must be strictly positive (> 0)")
        return v

    @field_validator("maker_fee", "taker_fee")
    @classmethod
    def validate_non_negative_fee(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Fee rate cannot be negative")
        return v

    @model_validator(mode="after")
    def validate_base_quote_match(self) -> Self:
        expected_symbol = f"{self.base_asset.upper()}/{self.quote_asset.upper()}"
        if self.symbol != expected_symbol:
            raise ValueError(
                f"Symbol '{self.symbol}' does not match base/quote '{expected_symbol}'"
            )
        if self.base_asset.upper() == self.quote_asset.upper():
            raise ValueError("Base asset and quote asset cannot be identical")
        return self


# ============================================================================
# 3. Candle Model
# ============================================================================


class Candle(BaseModel):
    """
    OHLCV Candlestick data model.
    """

    symbol: str = Field(description="Market symbol, e.g. BTC/USDT")
    timeframe: str = Field(default="1h", description="Candle interval, e.g. 1m, 1h, 1d")
    open_time: datetime = Field(description="Candle open timestamp (UTC)")
    close_time: datetime = Field(description="Candle close timestamp (UTC)")

    open: Decimal = Field(description="Opening price")
    high: Decimal = Field(description="Highest price")
    low: Decimal = Field(description="Lowest price")
    close: Decimal = Field(description="Closing price")
    volume: Decimal = Field(description="Trading volume")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        symbol = v.strip().upper()
        if not MARKET_SYMBOL_REGEX.match(symbol):
            raise ValueError(f"Invalid symbol '{v}'. Must be e.g. BTC/USDT")
        return symbol

    @field_validator("open", "high", "low", "close")
    @classmethod
    def validate_positive_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Candle prices must be strictly positive (> 0)")
        return v

    @field_validator("volume")
    @classmethod
    def validate_non_negative_volume(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Candle volume cannot be negative")
        return v

    @model_validator(mode="after")
    def validate_ohlc_consistency(self) -> Self:
        if self.high < self.low:
            raise ValueError(f"High price ({self.high}) cannot be less than low price ({self.low})")
        if self.high < self.open or self.high < self.close:
            raise ValueError(f"High price ({self.high}) must be >= open ({self.open}) and close ({self.close})")
        if self.low > self.open or self.low > self.close:
            raise ValueError(f"Low price ({self.low}) must be <= open ({self.open}) and close ({self.close})")
        if self.close_time < self.open_time:
            raise ValueError(f"Close time ({self.close_time}) cannot be before open time ({self.open_time})")
        return self


# ============================================================================
# 4. Ticker Model
# ============================================================================


class Ticker(BaseModel):
    """
    Real-time price snapshot model.
    """

    symbol: str = Field(description="Market symbol, e.g. BTC/USDT")
    last_price: Decimal = Field(description="Most recent trade price")
    bid_price: Decimal = Field(description="Best bid price")
    ask_price: Decimal = Field(description="Best ask price")
    volume_24h: Decimal = Field(default=Decimal("0"), description="24-hour volume")
    high_24h: Decimal | None = Field(default=None, description="24-hour high price")
    low_24h: Decimal | None = Field(default=None, description="24-hour low price")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        symbol = v.strip().upper()
        if not MARKET_SYMBOL_REGEX.match(symbol):
            raise ValueError(f"Invalid symbol '{v}'")
        return symbol

    @field_validator("last_price", "bid_price", "ask_price")
    @classmethod
    def validate_positive_prices(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Prices must be strictly positive (> 0)")
        return v

    @field_validator("volume_24h")
    @classmethod
    def validate_volume(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Volume cannot be negative")
        return v

    @model_validator(mode="after")
    def validate_spread(self) -> Self:
        if self.bid_price > self.ask_price:
            raise ValueError(f"Bid price ({self.bid_price}) cannot exceed ask price ({self.ask_price})")
        if self.high_24h is not None and self.low_24h is not None:
            if self.high_24h < self.low_24h:
                raise ValueError("24h High price cannot be lower than 24h Low price")
        return self


# ============================================================================
# 5. Signal Model
# ============================================================================


class SignalModel(BaseModel):
    """
    Strategy output signal model.
    """

    symbol: str = Field(description="Market symbol, e.g. BTC/USDT")
    direction: Signal = Field(description="Signal direction (BUY, SELL, HOLD)")
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="Signal strength 0.0 to 1.0")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Signal confidence 0.0 to 1.0")

    target_price: Decimal | None = Field(default=None, description="Optional target price")
    stop_loss: Decimal | None = Field(default=None, description="Optional stop loss price")
    take_profit: Decimal | None = Field(default=None, description="Optional take profit price")

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        symbol = v.strip().upper()
        if not MARKET_SYMBOL_REGEX.match(symbol):
            raise ValueError(f"Invalid symbol '{v}'")
        return symbol

    @field_validator("target_price", "stop_loss", "take_profit")
    @classmethod
    def validate_optional_prices(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Price targets must be strictly positive (> 0)")
        return v


# ============================================================================
# 6. Order Model
# ============================================================================


class Order(BaseModel):
    """
    Order intent and state lifecycle model.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str = Field(description="Market symbol, e.g. BTC/USDT")
    side: OrderSide = Field(description="Order side (BUY or SELL)")
    order_type: OrderType = Field(description="Order type (MARKET or LIMIT)")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order lifecycle status")

    quantity: Decimal = Field(description="Order quantity")
    price: Decimal | None = Field(default=None, description="Price for LIMIT orders")
    filled_quantity: Decimal = Field(default=Decimal("0"), description="Quantity filled so far")
    stop_price: Decimal | None = Field(default=None, description="Stop trigger price")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        symbol = v.strip().upper()
        if not MARKET_SYMBOL_REGEX.match(symbol):
            raise ValueError(f"Invalid market symbol '{v}'")
        return symbol

    @field_validator("quantity")
    @classmethod
    def validate_positive_quantity(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Order quantity must be strictly positive (> 0)")
        return v

    @field_validator("filled_quantity")
    @classmethod
    def validate_non_negative_filled_qty(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Filled quantity cannot be negative")
        return v

    @field_validator("price", "stop_price")
    @classmethod
    def validate_optional_positive_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Order prices must be strictly positive (> 0)")
        return v

    @model_validator(mode="after")
    def validate_order_requirements(self) -> Self:
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("LIMIT orders require a price")
        if self.filled_quantity > self.quantity:
            raise ValueError(
                f"Filled quantity ({self.filled_quantity}) cannot exceed order quantity ({self.quantity})"
            )
        return self

    def can_transition_to(self, new_status: OrderStatus) -> bool:
        """
        Validate valid status transitions:
        PENDING -> FILLED, PARTIALLY_FILLED, CANCELLED, REJECTED
        PARTIALLY_FILLED -> FILLED, CANCELLED, REJECTED
        FILLED, CANCELLED, REJECTED -> Terminal (no transition)
        """
        if self.status == new_status:
            return True

        allowed: dict[OrderStatus, set[OrderStatus]] = {
            OrderStatus.PENDING: {
                OrderStatus.FILLED,
                OrderStatus.PARTIALLY_FILLED,
                OrderStatus.CANCELLED,
                OrderStatus.REJECTED,
            },
            OrderStatus.PARTIALLY_FILLED: {
                OrderStatus.FILLED,
                OrderStatus.CANCELLED,
                OrderStatus.REJECTED,
            },
            OrderStatus.FILLED: set(),
            OrderStatus.CANCELLED: set(),
            OrderStatus.REJECTED: set(),
        }

        return new_status in allowed.get(self.status, set())


# ============================================================================
# 7. Trade Model
# ============================================================================


class Trade(BaseModel):
    """
    Executed trade / fill model.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    order_id: str = Field(description="Parent order ID")
    symbol: str = Field(description="Market symbol, e.g. BTC/USDT")
    side: OrderSide = Field(description="Trade side (BUY or SELL)")
    price: Decimal = Field(description="Execution price")
    quantity: Decimal = Field(description="Executed quantity")
    fee: Decimal = Field(default=Decimal("0"), description="Trade fee paid")
    fee_currency: str = Field(default="USDT", description="Currency of fee")
    slippage: Decimal = Field(default=Decimal("0"), description="Execution slippage")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        symbol = v.strip().upper()
        if not MARKET_SYMBOL_REGEX.match(symbol):
            raise ValueError(f"Invalid market symbol '{v}'")
        return symbol

    @field_validator("price", "quantity")
    @classmethod
    def validate_positive_values(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price and quantity must be strictly positive (> 0)")
        return v

    @field_validator("fee", "slippage")
    @classmethod
    def validate_non_negative_values(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Fee and slippage cannot be negative")
        return v


# ============================================================================
# 8. Position Model
# ============================================================================


class Position(BaseModel):
    """
    Trading position model.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str = Field(description="Market symbol, e.g. BTC/USDT")
    side: PositionSide = Field(default=PositionSide.LONG, description="Position side")
    quantity: Decimal = Field(description="Position quantity")
    entry_price: Decimal = Field(description="Average entry price")
    current_price: Decimal = Field(description="Current market price")

    unrealized_pnl: Decimal = Field(default=Decimal("0"))
    realized_pnl: Decimal = Field(default=Decimal("0"))

    status: PositionStatus = Field(default=PositionStatus.OPEN)
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: datetime | None = Field(default=None)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        symbol = v.strip().upper()
        if not MARKET_SYMBOL_REGEX.match(symbol):
            raise ValueError(f"Invalid market symbol '{v}'")
        return symbol

    @field_validator("quantity")
    @classmethod
    def validate_non_negative_qty(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Position quantity cannot be negative")
        return v

    @field_validator("entry_price", "current_price")
    @classmethod
    def validate_positive_prices(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Position prices must be strictly positive (> 0)")
        return v

    def calculate_unrealized_pnl(self) -> Decimal:
        """Calculate unrealized PnL based on current price and entry price."""
        if self.side == PositionSide.LONG:
            return (self.current_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - self.current_price) * self.quantity


# ============================================================================
# 9. Portfolio Model
# ============================================================================


class Portfolio(BaseModel):
    """
    Portfolio valuation and state model.
    """

    account_id: str = Field(description="Associated account ID")
    cash_balance: Decimal = Field(default=Decimal("10000.0"), description="Available cash in quote currency")
    total_equity: Decimal = Field(default=Decimal("10000.0"), description="Total equity (cash + unrealized PnL)")
    unrealized_pnl: Decimal = Field(default=Decimal("0"))
    realized_pnl: Decimal = Field(default=Decimal("0"))

    positions: dict[str, Position] = Field(default_factory=dict, description="Active positions by symbol")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("cash_balance", "total_equity")
    @classmethod
    def validate_non_negative_balances(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Portfolio cash and total equity cannot be negative")
        return v


# ============================================================================
# 10. Account Model
# ============================================================================


class Account(BaseModel):
    """
    Account model representing a trading balance account.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="Primary Account", description="Account display name")
    currency: str = Field(default="USDT", description="Base balance currency")

    balance: Decimal = Field(default=Decimal("10000.0"), description="Total account balance")
    available_balance: Decimal = Field(
        default=Decimal("10000.0"), description="Available unencumbered balance"
    )
    locked_balance: Decimal = Field(
        default=Decimal("0.0"), description="Balance locked in open orders"
    )

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        code = v.strip().upper()
        if not ASSET_CODE_REGEX.match(code):
            raise ValueError(f"Invalid currency code '{v}'")
        return code

    @field_validator("balance", "available_balance", "locked_balance")
    @classmethod
    def validate_non_negative_balances(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Account balances cannot be negative")
        return v

    @model_validator(mode="after")
    def validate_balance_sum(self) -> Self:
        expected_total = self.available_balance + self.locked_balance
        if self.balance != expected_total:
            raise ValueError(
                f"Account balance ({self.balance}) does not equal available ({self.available_balance}) + locked ({self.locked_balance})"
            )
        return self


# ============================================================================
# 11. BacktestResult Model
# ============================================================================


class BacktestResultDomain(BaseModel):
    """
    Backtest execution result domain model.
    """

    id: str | int | None = None
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime

    initial_capital: Decimal = Field(default=Decimal("10000.0"))
    final_equity: Decimal = Field(default=Decimal("10000.0"))

    total_return_pct: float = 0.0
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    profit_factor: float | None = None
    avg_trade_duration_hours: float | None = None

    equity_curve: list[dict[str, Any]] = Field(default_factory=list)
    trade_log: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Alias for domain export
BacktestResultModel = BacktestResultDomain
