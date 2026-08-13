"""
BETHBot — Pydantic schemas: Asset.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    """Asset response schema."""

    id: int
    symbol: str
    base_currency: str
    quote_currency: str
    exchange: str
    asset_type: str
    tick_size: Decimal
    lot_size: Decimal
    min_notional: Decimal
    maker_fee: Decimal
    taker_fee: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetCreate(BaseModel):
    """Asset creation schema."""

    symbol: str = Field(description="Trading pair, e.g. BTC/USDT")
    base_currency: str
    quote_currency: str
    exchange: str = "binance"
    asset_type: str = "SPOT"
    tick_size: Decimal = Decimal("0.01")
    lot_size: Decimal = Decimal("0.00001")
    min_notional: Decimal = Decimal("10.0")
