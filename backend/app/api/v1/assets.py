"""
BETHBot — Asset endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.core.dependencies import DBSession
from app.models.asset import Asset
from app.schemas.asset import AssetResponse

router = APIRouter()


@router.get("", response_model=list[AssetResponse])
async def list_assets(session: DBSession) -> list:
    """List all supported trading pairs."""
    result = await session.execute(select(Asset).where(Asset.is_active == True).order_by(Asset.symbol))
    assets = result.scalars().all()
    return assets


@router.get("/{symbol}")
async def get_asset(symbol: str, session: DBSession) -> dict:
    """Get details for a specific trading pair."""
    # Support both 'BTCUSDT' and 'BTC/USDT' format
    normalized = symbol if "/" in symbol else f"{symbol[:3]}/{symbol[3:]}" if len(symbol) > 3 else symbol
    result = await session.execute(select(Asset).where(Asset.symbol == normalized))
    asset = result.scalar_one_or_none()
    if not asset:
        return {"error": "Asset not found", "symbol": normalized}
    return {
        "id": asset.id,
        "symbol": asset.symbol,
        "base_currency": asset.base_currency,
        "quote_currency": asset.quote_currency,
        "exchange": asset.exchange,
        "is_active": asset.is_active,
    }
