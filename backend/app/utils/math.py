"""
BETHBot — Utility: Financial math helpers.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN


def pct_change(old: Decimal, new: Decimal) -> Decimal:
    """Calculate percentage change from old to new."""
    if old == 0:
        return Decimal("0")
    return ((new - old) / old) * Decimal("100")


def round_decimal(value: Decimal, precision: int = 8) -> Decimal:
    """Round a Decimal to the given precision."""
    quantizer = Decimal(10) ** -precision
    return value.quantize(quantizer, rounding=ROUND_DOWN)
