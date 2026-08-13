"""
BETHBot — Asset abstraction.

Provides a pure-data TradingPair model for the engine layer.
No database or HTTP dependencies — this is pure logic.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN
from enum import StrEnum

from pydantic import BaseModel, Field


class AssetType(StrEnum):
    """Supported asset types. Extensible for futures/perpetuals."""

    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"
    FUTURES = "FUTURES"


class TradingPair(BaseModel):
    """
    Immutable representation of a tradable instrument.

    This is the engine's view of an asset — no ORM, no DB.
    Services convert between ORM Asset and this model.
    """

    symbol: str = Field(description="Trading pair symbol, e.g. BTC/USDT")
    base: str = Field(description="Base currency, e.g. BTC")
    quote: str = Field(description="Quote currency, e.g. USDT")
    exchange: str = Field(default="binance", description="Exchange name")
    asset_type: AssetType = AssetType.SPOT

    # Precision rules
    tick_size: Decimal = Field(
        default=Decimal("0.01"), description="Minimum price increment"
    )
    lot_size: Decimal = Field(
        default=Decimal("0.00001"), description="Minimum quantity increment"
    )
    min_notional: Decimal = Field(
        default=Decimal("10.0"), description="Minimum order value in quote currency"
    )

    # Fee schedule
    maker_fee: Decimal = Field(default=Decimal("0.001"), description="Maker fee rate (0.1%)")
    taker_fee: Decimal = Field(default=Decimal("0.001"), description="Taker fee rate (0.1%)")

    def round_price(self, price: Decimal) -> Decimal:
        """Round price down to valid tick size."""
        if self.tick_size == 0:
            return price
        return (price / self.tick_size).to_integral_value(rounding=ROUND_DOWN) * self.tick_size

    def round_quantity(self, qty: Decimal) -> Decimal:
        """Round quantity down to valid lot size."""
        if self.lot_size == 0:
            return qty
        return (qty / self.lot_size).to_integral_value(rounding=ROUND_DOWN) * self.lot_size

    def validate_order(self, price: Decimal, quantity: Decimal) -> tuple[bool, str]:
        """
        Check if an order meets minimum notional and precision rules.

        Returns:
            (is_valid, reason) tuple
        """
        notional = price * quantity
        if notional < self.min_notional:
            return False, (
                f"Order notional {notional} below minimum {self.min_notional} {self.quote}"
            )
        if quantity <= 0:
            return False, "Quantity must be positive"
        if price <= 0:
            return False, "Price must be positive"
        return True, "OK"

    def calculate_fee(self, price: Decimal, quantity: Decimal, is_maker: bool = False) -> Decimal:
        """Calculate the fee for a trade."""
        fee_rate = self.maker_fee if is_maker else self.taker_fee
        return price * quantity * fee_rate

    @classmethod
    def from_symbol(cls, symbol: str, exchange: str = "binance") -> TradingPair:
        """
        Create a TradingPair from a symbol string.
        Uses sensible defaults — real values should come from exchange info.
        """
        parts = symbol.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid symbol format: {symbol}. Expected 'BASE/QUOTE'.")
        return cls(
            symbol=symbol,
            base=parts[0],
            quote=parts[1],
            exchange=exchange,
        )
