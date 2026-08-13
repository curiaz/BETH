"""
BETHBot — Application lifecycle events.

Startup: initialize database, logging, strategy registry.
Shutdown: close database connections, cleanup resources.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle manager."""

    # --- Startup ---
    setup_logging()
    logger.info("bethbot.starting", app_name="BETHBot")

    # Initialize database
    from app.core.config import settings
    from app.core.database import init_db, close_db

    if settings.is_development:
        await init_db()
        logger.info("bethbot.database_initialized", mode="development")
    else:
        logger.info("bethbot.database_ready", note="Use 'alembic upgrade head' for migrations")

    logger.info(
        "bethbot.started",
        trading_mode=settings.trading_mode,
        symbols=settings.symbols_list,
        exchange=settings.exchange,
    )

    yield

    # --- Shutdown ---
    logger.info("bethbot.shutting_down")
    await close_db()
    logger.info("bethbot.stopped")
