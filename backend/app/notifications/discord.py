"""
BETHBot — Discord Notification Provider.

Implements BaseNotifier using Discord Webhooks.
Color-coded embeds for trading signals, paper trade executions, risk rejections,
market data failures, and emergency stops.

SECURITY INVARIANT: The DISCORD_WEBHOOK_URL is NEVER logged or exposed.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.logging import get_logger
from app.notifications.base import BaseNotifier, NotificationEvent, NotificationType

logger = get_logger(__name__)

# Discord embed color constants (decimal RGB)
DISCORD_COLORS: dict[NotificationType, int] = {
    NotificationType.BOT_STARTED: 0x3B82F6,  # Blue
    NotificationType.BOT_STOPPED: 0x64748B,  # Slate Gray
    NotificationType.BUY_SIGNAL: 0x10B981,  # Emerald Green
    NotificationType.SELL_SIGNAL: 0x06B6D4,  # Cyan
    NotificationType.PAPER_TRADE_EXECUTED: 0x10B981,  # Green
    NotificationType.TRADE_CLOSED: 0x8B5CF6,  # Purple
    NotificationType.RISK_REJECTION: 0xF59E0B,  # Amber
    NotificationType.MARKET_DATA_FAILURE: 0xEF4444,  # Red
    NotificationType.EXCHANGE_CONNECTION_FAILURE: 0xEF4444,  # Red
    NotificationType.UNEXPECTED_EXCEPTION: 0xDC2626,  # Dark Red
    NotificationType.DAILY_LOSS_LIMIT_REACHED: 0xDC2626,  # Dark Red
    NotificationType.EMERGENCY_STOP: 0x991B1B,  # Crimson
}


def mask_webhook_url(url: str | None) -> str:
    """Mask webhook URL for safe logging/repr."""
    if not url:
        return "[NOT_SET]"
    if "webhooks/" in url:
        base_part = url.split("webhooks/")[0]
        return f"{base_part}webhooks/****"
    return "*****"


class DiscordNotifier(BaseNotifier):
    """
    Discord Webhook Notifier Implementation.

    Sends structured, color-coded embeds to Discord webhook channels safely.
    """

    def __init__(
        self,
        webhook_url: str,
        timeout: float = 5.0,
        client: httpx.AsyncClient | None = None,
    ):
        self._webhook_url = webhook_url.strip() if webhook_url else ""
        self._timeout = timeout
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(timeout))
        self._owns_client = client is None

    @property
    def name(self) -> str:
        return "discord"

    def __repr__(self) -> str:
        return f"<DiscordNotifier url={mask_webhook_url(self._webhook_url)}>"

    async def send(self, event: NotificationEvent) -> bool:
        """
        Send notification event as a Discord embed.
        """
        if not self._webhook_url:
            logger.debug("discord_notifier.skipped_no_url")
            return False

        color = DISCORD_COLORS.get(event.event_type, 0x3B82F6)

        fields = [
            {"name": k.replace("_", " ").title(), "value": str(v), "inline": True}
            for k, v in event.details.items()
        ]

        embed = {
            "title": f"[{event.event_type.value}] {event.title}",
            "description": event.message,
            "color": color,
            "fields": fields,
            "footer": {"text": "Quantara BETHBot Trading Engine"},
            "timestamp": event.timestamp.isoformat(),
        }

        payload = {"embeds": [embed]}

        try:
            response = await self._client.post(self._webhook_url, json=payload)
            if response.status_code in (200, 204):
                logger.info(
                    "discord_notifier.sent_success",
                    event_type=event.event_type.value,
                    title=event.title,
                )
                return True
            else:
                logger.warning(
                    "discord_notifier.send_failed_status",
                    status_code=response.status_code,
                    event_type=event.event_type.value,
                )
                return False
        except Exception as e:
            logger.warning(
                "discord_notifier.send_exception",
                event_type=event.event_type.value,
                error=str(e),
            )
            return False

    async def close(self) -> None:
        """Close httpx AsyncClient resources."""
        if self._owns_client and not self._client.is_closed:
            await self._client.aclose()
