"""
BETHBot — Notification provider interface.

All notification-specific code is isolated behind this abstraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    """
    Abstract notification provider.

    Implementations: DiscordNotifier, TelegramNotifier (future), EmailNotifier (future).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @abstractmethod
    async def send(
        self,
        title: str,
        message: str,
        level: str = "info",
    ) -> bool:
        """
        Send a notification.

        Args:
            title: Notification title/subject
            message: Notification body
            level: Severity level (info, warning, error, critical)

        Returns:
            True if sent successfully, False otherwise
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Cleanup resources."""
        ...
