"""
BETHBot — Portfolio endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import DBSession
from app.models.portfolio import PortfolioSnapshot
from app.models.position import Position

router = APIRouter()


@router.get("")
async def get_portfolio(
    session: DBSession,
    session_type: str = Query(default="PAPER"),
) -> dict:
    """Get current portfolio state."""
    # Get latest snapshot
    result = await session.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.session_type == session_type)
        .order_by(PortfolioSnapshot.snapshot_at.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()

    # Get open positions
    pos_result = await session.execute(
        select(Position)
        .where(Position.session_type == session_type, Position.status == "OPEN")
    )
    positions = pos_result.scalars().all()

    return {
        "total_equity": float(snapshot.total_equity) if snapshot else 0,
        "cash_balance": float(snapshot.cash_balance) if snapshot else 0,
        "unrealized_pnl": float(snapshot.unrealized_pnl) if snapshot else 0,
        "realized_pnl": float(snapshot.realized_pnl) if snapshot else 0,
        "positions": [
            {
                "asset_id": p.asset_id,
                "side": p.side,
                "quantity": float(p.quantity),
                "entry_price": float(p.entry_price),
                "current_price": float(p.current_price),
                "unrealized_pnl": float(p.unrealized_pnl),
                "status": p.status,
            }
            for p in positions
        ],
        "session_type": session_type,
    }


@router.get("/history")
async def get_equity_history(
    session: DBSession,
    session_type: str = Query(default="PAPER"),
    limit: int = Query(default=500, ge=1, le=5000),
) -> list[dict]:
    """Get portfolio equity curve."""
    result = await session.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.session_type == session_type)
        .order_by(PortfolioSnapshot.snapshot_at)
        .limit(limit)
    )
    snapshots = result.scalars().all()

    return [
        {
            "timestamp": s.snapshot_at.isoformat() if s.snapshot_at else None,
            "equity": float(s.total_equity),
            "cash": float(s.cash_balance),
        }
        for s in snapshots
    ]
