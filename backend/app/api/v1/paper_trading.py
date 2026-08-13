"""
BETHBot — Paper trading endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/status")
async def paper_trading_status() -> dict:
    """Get paper trading session status."""
    return {
        "mode": settings.trading_mode,
        "initial_balance": settings.paper_initial_balance,
        "status": "idle",
        "message": "Paper trading session management will be fully implemented in Phase 1.5",
    }


@router.post("/start")
async def start_paper_trading() -> dict:
    """Start a paper trading session."""
    return {
        "status": "started",
        "mode": "paper",
        "initial_balance": settings.paper_initial_balance,
        "message": "Paper trading session started (placeholder — full orchestration in Phase 1.5)",
    }


@router.post("/stop")
async def stop_paper_trading() -> dict:
    """Stop a paper trading session."""
    return {
        "status": "stopped",
        "message": "Paper trading session stopped (placeholder)",
    }
