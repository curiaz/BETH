"""
BETHBot — API router aggregator.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import assets, backtests, candles, orders, paper_trading, portfolio, strategies, system

api_router = APIRouter()

# v1 routes
api_router.include_router(system.router, prefix="/v1/system", tags=["system"])
api_router.include_router(assets.router, prefix="/v1/assets", tags=["assets"])
api_router.include_router(candles.router, prefix="/v1/candles", tags=["candles"])
api_router.include_router(strategies.router, prefix="/v1/strategies", tags=["strategies"])
api_router.include_router(backtests.router, prefix="/v1/backtests", tags=["backtests"])
api_router.include_router(paper_trading.router, prefix="/v1/paper-trading", tags=["paper-trading"])
api_router.include_router(orders.router, prefix="/v1/orders", tags=["orders"])
api_router.include_router(portfolio.router, prefix="/v1/portfolio", tags=["portfolio"])
