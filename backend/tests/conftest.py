"""
BETHBot — Test fixtures.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    """Create an in-memory SQLite async engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async session for testing."""
    session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing."""
    import pandas as pd
    import numpy as np
    from datetime import datetime, timezone, timedelta

    np.random.seed(42)
    dates = pd.date_range(
        start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        periods=200,
        freq="h",
    )

    # Generate realistic-ish price data
    price = 42000.0
    prices = []
    for _ in range(200):
        price *= 1 + np.random.normal(0, 0.005)
        prices.append(price)

    data = pd.DataFrame(
        {
            "open": prices,
            "high": [p * (1 + abs(np.random.normal(0, 0.003))) for p in prices],
            "low": [p * (1 - abs(np.random.normal(0, 0.003))) for p in prices],
            "close": [p * (1 + np.random.normal(0, 0.001)) for p in prices],
            "volume": [abs(np.random.normal(100, 30)) for _ in prices],
        },
        index=dates,
    )
    return data
