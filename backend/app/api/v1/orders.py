"""
BETHBot — Order endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import DBSession
from app.models.order import Order

router = APIRouter()


@router.get("")
async def list_orders(
    session: DBSession,
    session_type: str = Query(default="PAPER"),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict]:
    """List orders with optional filters."""
    query = (
        select(Order)
        .where(Order.session_type == session_type)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    if status:
        query = query.where(Order.status == status)

    result = await session.execute(query)
    orders = result.scalars().all()

    return [
        {
            "id": o.id,
            "asset_id": o.asset_id,
            "side": o.side,
            "order_type": o.order_type,
            "quantity": float(o.quantity),
            "price": float(o.price) if o.price else None,
            "status": o.status,
            "session_type": o.session_type,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]
