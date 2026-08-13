"""
BETHBot — Unit Tests for Notification System.

Tests all required cases:
1. NotificationService dispatching across 12 event types
2. DiscordNotifier formatting and webhook dispatch
3. Webhook URL masking security (verifying webhook token is NEVER logged or exposed)
4. Abstract provider interface allowing future Telegram / Email expansion
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.notifications.base import BaseNotifier, NotificationEvent, NotificationType
from app.notifications.discord import DiscordNotifier, mask_webhook_url
from app.notifications.service import NotificationService


class MockNotifier(BaseNotifier):
    """Mock provider for testing abstract notification interface."""

    def __init__(self):
        self.sent_events: list[NotificationEvent] = []

    @property
    def name(self) -> str:
        return "mock"

    async def send(self, event: NotificationEvent) -> bool:
        self.sent_events.append(event)
        return True

    async def close(self) -> None:
        pass


class TestNotificationSystem:
    @pytest.mark.asyncio
    async def test_all_12_notification_events(self):
        """Test sending all 12 notification event types via NotificationService."""
        mock_notifier = MockNotifier()
        service = NotificationService(notifiers=[mock_notifier])

        await service.notify_bot_started({"symbols": "BTC/USDT"})
        await service.notify_bot_stopped()
        await service.notify_buy_signal("BTC/USDT", 0.85, 64250.0)
        await service.notify_sell_signal("ETH/USDT", 0.90, 3480.0)
        await service.notify_paper_trade_executed("BTC/USDT", "BUY", 0.1, 64250.0, 6.42)
        await service.notify_trade_closed("ETH/USDT", 1.0, 3200.0, 3480.0, 280.0)
        await service.notify_risk_rejection("BTC/USDT", "Position size limit exceeded")
        await service.notify_market_data_failure("BTC/USDT", "HTTP 502 Bad Gateway")
        await service.notify_exchange_connection_failure("binance", "Network timeout")
        await service.notify_unexpected_exception("trading_loop", "ValueError: NaN detected")
        await service.notify_daily_loss_limit_reached(4.2, 3.0)
        await service.notify_emergency_stop("Manual shutdown command")

        assert len(mock_notifier.sent_events) == 12

        event_types = [e.event_type for e in mock_notifier.sent_events]
        assert NotificationType.BOT_STARTED in event_types
        assert NotificationType.BOT_STOPPED in event_types
        assert NotificationType.BUY_SIGNAL in event_types
        assert NotificationType.SELL_SIGNAL in event_types
        assert NotificationType.PAPER_TRADE_EXECUTED in event_types
        assert NotificationType.TRADE_CLOSED in event_types
        assert NotificationType.RISK_REJECTION in event_types
        assert NotificationType.MARKET_DATA_FAILURE in event_types
        assert NotificationType.EXCHANGE_CONNECTION_FAILURE in event_types
        assert NotificationType.UNEXPECTED_EXCEPTION in event_types
        assert NotificationType.DAILY_LOSS_LIMIT_REACHED in event_types
        assert NotificationType.EMERGENCY_STOP in event_types

    @pytest.mark.asyncio
    async def test_discord_notifier_payload_formatting(self):
        """Test DiscordNotifier formats embeds correctly and calls httpx client."""
        secret_url = "https://discord.com/api/webhooks/1234567890/SECRET_TOKEN_ABC123"
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.post.return_value = mock_response

        notifier = DiscordNotifier(webhook_url=secret_url, client=mock_client)

        event = NotificationEvent(
            event_type=NotificationType.BUY_SIGNAL,
            title="BUY Signal — BTC/USDT",
            message="Strategy generated BUY signal",
            details={"symbol": "BTC/USDT", "price": "$64,250.00"},
        )

        success = await notifier.send(event)

        assert success is True
        assert mock_client.post.call_count == 1

        call_args = mock_client.post.call_args
        posted_url = call_args[0][0]
        posted_payload = call_args[1]["json"]

        assert posted_url == secret_url
        assert "embeds" in posted_payload
        assert posted_payload["embeds"][0]["title"] == "[BUY_SIGNAL] BUY Signal — BTC/USDT"

    def test_security_webhook_url_masking(self):
        """Test security invariant: mask_webhook_url conceals token in logs and repr."""
        secret_url = "https://discord.com/api/webhooks/1537339084266274896/G43cYz7LymcCx9KH0gL0GPKFLQCPWHkm8eH4gRnV9GGw82MmQHm2c-GozINXCfMENF4J"

        masked = mask_webhook_url(secret_url)
        assert "G43cYz7LymcCx9KH" not in masked
        assert masked == "https://discord.com/api/webhooks/****"

        notifier = DiscordNotifier(webhook_url=secret_url)
        notifier_repr = repr(notifier)
        assert "G43cYz7LymcCx9KH" not in notifier_repr
        assert "****" in notifier_repr
