"""
BETHBot — Execution abstractions.

OrderRequest, Fill, and BaseExecutionHandler define the contract
for all execution modes (backtest, paper, live).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from uuid import uuid4


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class OrderRequest:
    """
    Intent to trade — created by the strategy runner after risk approval.
    This is the input to an execution handler.
    """

    asset_symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None  # Required for LIMIT
    stop_price: Decimal | None = None  # Required for STOP
    time_in_force: str = "GTC"
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class Fill:
    """
    Result of an order execution.
    Returned by execution handlers after processing an OrderRequest.
    """

    order_id: str
    asset_symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fee: Decimal
    slippage: Decimal
    timestamp: datetime
    status: OrderStatus = OrderStatus.FILLED

    @property
    def net_value(self) -> Decimal:
        """Net value of the fill (price * quantity - fee)."""
        return self.price * self.quantity - self.fee


class BaseExecutionHandler(ABC):
    """
    Abstract execution handler.

    Implementations:
      - BacktestExecutor: simulated fills against historical data
      - PaperExecutor: simulated fills against live market prices
      - LiveExecutor: real orders (stub — raises NotImplementedError)
    """

    @abstractmethod
    async def submit_order(self, order: OrderRequest) -> Fill:
        """Submit an order and return the fill result."""
        ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order. Returns True if successfully cancelled."""
        ...

    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Query the current status of an order."""
        ...
