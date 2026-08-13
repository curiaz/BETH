"""
BETHBot — FastAPI application entry point.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.events import lifespan
from app.core.exceptions import (
    BETHBotError,
    LiveTradingDisabledError,
    RiskViolationError,
    TradingError,
)
from app.api.router import api_router

app = FastAPI(
    title=settings.app_name,
    description="Professional algorithmic trading platform for BTC/USDT and ETH/USDT",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")


# --- Exception Handlers ---


@app.exception_handler(LiveTradingDisabledError)
async def live_trading_handler(request: Request, exc: LiveTradingDisabledError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"error": "forbidden", "detail": exc.message},
    )


@app.exception_handler(RiskViolationError)
async def risk_violation_handler(request: Request, exc: RiskViolationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": "risk_violation",
            "detail": exc.message,
            "rule": exc.rule_name,
        },
    )


@app.exception_handler(TradingError)
async def trading_error_handler(request: Request, exc: TradingError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": "trading_error", "detail": exc.message},
    )


@app.exception_handler(BETHBotError)
async def bethbot_error_handler(request: Request, exc: BETHBotError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": exc.message},
    )
