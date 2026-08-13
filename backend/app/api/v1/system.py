"""
BETHBot — System endpoints (health, status).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name, "version": "0.1.0"}


@router.get("/status")
async def system_status() -> dict:
    """System status with configuration summary."""
    return {
        "app_name": settings.app_name,
        "version": "0.1.0",
        "environment": settings.app_env,
        "trading_mode": settings.trading_mode,
        "exchange": settings.exchange,
        "supported_symbols": settings.symbols_list,
        "default_timeframe": settings.default_timeframe,
        "paper_initial_balance": settings.paper_initial_balance,
    }
