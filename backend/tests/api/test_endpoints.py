"""
BETHBot — API tests: Endpoint contracts.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_health_check():
    """Test /api/v1/system/health returns healthy."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "BETHBot"


@pytest.mark.asyncio
async def test_system_status():
    """Test /api/v1/system/status returns configuration."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["trading_mode"] == "paper"
        assert "supported_symbols" in data


@pytest.mark.asyncio
async def test_list_strategies():
    """Test /api/v1/strategies returns strategy list."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/strategies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # sma_crossover + rsi_mean_reversion
        names = [s["name"] for s in data]
        assert "sma_crossover" in names
        assert "rsi_mean_reversion" in names


@pytest.mark.asyncio
async def test_paper_trading_status():
    """Test /api/v1/paper-trading/status."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/paper-trading/status")
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "paper"
