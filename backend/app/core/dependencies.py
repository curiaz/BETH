"""
BETHBot — FastAPI dependency injection factories.

These are used with FastAPI's Depends() system to inject
database sessions, services, and configuration into route handlers.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.core.database import get_db_session


# --- Database Session ---

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async for session in get_db_session():
        yield session


DBSession = Annotated[AsyncSession, Depends(get_session)]


# --- Configuration ---

def get_settings() -> Settings:
    """Return the application settings singleton."""
    return settings


AppSettings = Annotated[Settings, Depends(get_settings)]
