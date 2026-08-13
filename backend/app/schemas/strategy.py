"""
BETHBot — Pydantic schemas: Strategy.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class StrategyParameterResponse(BaseModel):
    """Strategy parameter description for UI rendering."""

    name: str
    type: str
    default: Any
    min_value: Any | None = None
    max_value: Any | None = None
    description: str = ""


class StrategyResponse(BaseModel):
    """Strategy information response."""

    name: str
    version: str
    description: str
    parameters: list[StrategyParameterResponse]
