"""
BETHBot — Notification System Base Interfaces.

Defines the contract for notification providers (Discord, Telegram, Email, etc.)
and standardized notification events across all system events.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class NotificationType(StrEnum):
    """Supported system notification types."""

    BOT_STARTED = "BOT_STARTED"
    BOT_STOPPED = "BOT_STOPPED"
    BUY_SIGNAL = "BUY_SIGNAL"
    SELL_SIGNAL = "SELL_SIGNAL"
    PAPER_TRADE_EXECUTED = "PAPER_TRADE_EXECUTED"
    TRADE_CLOSED = "TRADE_CLOSED"
    RISK_REJECTION = "RISK_REJECTION"
    MARKET_DATA_FAILURE = "MARKET_DATA_FAILURE"
    EXCHANGE_CONNECTION_FAILURE = "EXCHANGE_CONNECTION_FAILURE"
    UNEXPECTED_EXCEPTION = "UNEXPECTED_EXCEPTION"
    DAILY_LOSS_LIMIT_REACHED = "DAILY_LOSS_LIMIT_REACHED"
    EMERGENCY_STOP = "EMERGENCY_STOP"


@dataclass
class NotificationEvent:
    """
    Standardized payload for system notifications.
    """

    event_type: NotificationType
    title: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseNotifier(ABC):
    """
    Abstract notifier provider interface.

    Allows plugging in DiscordNotifier, and future TelegramNotifier or EmailNotifier cleanly.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider display name (e.g. 'discord')."""
        ...

    @abstractmethod
    async def send(self, event: NotificationEvent) -> bool:
        """
        Send a notification event asynchronously.

        Returns True if sent successfully, False otherwise.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close provider resources."""
        ...
