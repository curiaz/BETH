"""
BETHBot — Strategy endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.engine.strategy.registry import StrategyRegistry
from app.schemas.strategy import StrategyParameterResponse, StrategyResponse

router = APIRouter()


@router.get("", response_model=list[StrategyResponse])
async def list_strategies() -> list[StrategyResponse]:
    """List all registered trading strategies."""
    StrategyRegistry.initialize_builtin()
    strategies = []
    for name, cls in StrategyRegistry.list_all().items():
        params = [
            StrategyParameterResponse(
                name=p.name,
                type=p.type.value,
                default=p.default,
                min_value=p.min_value,
                max_value=p.max_value,
                description=p.description,
            )
            for p in cls.parameters()
        ]
        strategies.append(
            StrategyResponse(
                name=cls.name,
                version=cls.version,
                description=cls.description,
                parameters=params,
            )
        )
    return strategies
