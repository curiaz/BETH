"""
BETHBot — Discord notification provider.

Sends notifications via Discord webhooks.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.core.logging import get_logger
from app.integrations.notifications.base import NotificationProvider

logger = get_logger(__name__)

# Discord embed color mapping
LEVEL_COLORS = {
    "info": 0x3498DB,      # Blue
    "success": 0x2ECC71,   # Green
    "warning": 0xF39C12,   # Orange
    "error": 0xE74C3C,     # Red
    "critical": 0x992D22,  # Dark Red
}

LEVEL_EMOJIS = {
    "info": "ℹ️",
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "critical": "🚨",
}


class DiscordNotifier(NotificationProvider):
    """Sends notifications via Discord webhook with rich embeds."""

    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))

    @property
    def name(self) -> str:
        return "discord"

    async def send(
        self,
        title: str,
        message: str,
        level: str = "info",
    ) -> bool:
        """Send a Discord webhook notification with a rich embed."""
        if not self._webhook_url:
            logger.debug("discord.skipped", reason="No webhook URL configured")
            return False

        emoji = LEVEL_EMOJIS.get(level, "ℹ️")
        color = LEVEL_COLORS.get(level, 0x3498DB)

        payload = {
            "embeds": [
                {
                    "title": f"{emoji} {title}",
                    "description": message,
                    "color": color,
                    "footer": {"text": "BETHBot Trading Platform"},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }

        try:
            response = await self._client.post(self._webhook_url, json=payload)
            if response.status_code in (200, 204):
                logger.info("discord.sent", title=title, level=level)
                return True
            else:
                logger.warning(
                    "discord.failed",
                    status_code=response.status_code,
                    response=response.text[:200],
                )
                return False
        except Exception as e:
            logger.error("discord.error", error=str(e))
            return False

    async def close(self) -> None:
        """Close the httpx client."""
        await self._client.aclose()
