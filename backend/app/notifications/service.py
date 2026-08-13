"""
BETHBot — Notification Service.

High-level notification service dispatching events to all configured notifiers
(DiscordNotifier, and future Telegram / Email notifiers).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Sequence

from app.core.config import settings
from app.core.logging import get_logger
from app.notifications.base import BaseNotifier, NotificationEvent, NotificationType
from app.notifications.discord import DiscordNotifier, mask_webhook_url

logger = get_logger(__name__)


class NotificationService:
    """
    Central Notification Service.

    Coordinates sending system events to registered notification channels.
    """

    def __init__(self, notifiers: Sequence[BaseNotifier] | None = None):
        if notifiers is not None:
            self.notifiers: list[BaseNotifier] = list(notifiers)
        else:
            self.notifiers: list[BaseNotifier] = []
            webhook_url = getattr(settings, "discord_webhook_url", "")
            if webhook_url:
                self.notifiers.append(DiscordNotifier(webhook_url=webhook_url))

    def add_notifier(self, notifier: BaseNotifier) -> None:
        """Add a notification provider."""
        self.notifiers.append(notifier)

    async def notify(self, event: NotificationEvent) -> list[bool]:
        """
        Dispatch notification event to all registered providers asynchronously.
        """
        if not self.notifiers:
            logger.debug("notification_service.no_notifiers_configured", type=event.event_type.value)
            return []

        tasks = [n.send(event) for n in self.notifiers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = []
        for res in results:
            if isinstance(res, bool):
                successes.append(res)
            else:
                logger.warning("notification_service.provider_error", error=str(res))
                successes.append(False)

        return successes

    # =========================================================================
    # Convenience Notification Methods
    # =========================================================================

    async def notify_bot_started(self, details: dict[str, Any] | None = None) -> None:
        """Send BOT_STARTED notification."""
        event = NotificationEvent(
            event_type=NotificationType.BOT_STARTED,
            title="Trading Engine Started",
            message="Quantara paper trading engine has started successfully.",
            details=details or {"mode": settings.trading_mode.upper()},
        )
        await self.notify(event)

    async def notify_bot_stopped(self, details: dict[str, Any] | None = None) -> None:
        """Send BOT_STOPPED notification."""
        event = NotificationEvent(
            event_type=NotificationType.BOT_STOPPED,
            title="Trading Engine Stopped",
            message="Quantara paper trading engine has stopped.",
            details=details or {},
        )
        await self.notify(event)

    async def notify_buy_signal(self, symbol: str, strength: float, price: float) -> None:
        """Send BUY_SIGNAL notification."""
        event = NotificationEvent(
            event_type=NotificationType.BUY_SIGNAL,
            title=f"BUY Signal — {symbol}",
            message=f"Strategy generated BUY signal for {symbol} at ${price:,.2f}.",
            details={"symbol": symbol, "strength": f"{strength:.2f}", "price": f"${price:,.2f}"},
        )
        await self.notify(event)

    async def notify_sell_signal(self, symbol: str, strength: float, price: float) -> None:
        """Send SELL_SIGNAL notification."""
        event = NotificationEvent(
            event_type=NotificationType.SELL_SIGNAL,
            title=f"SELL Signal — {symbol}",
            message=f"Strategy generated SELL signal for {symbol} at ${price:,.2f}.",
            details={"symbol": symbol, "strength": f"{strength:.2f}", "price": f"${price:,.2f}"},
        )
        await self.notify(event)

    async def notify_paper_trade_executed(
        self, symbol: str, side: str, qty: float, price: float, fee: float
    ) -> None:
        """Send PAPER_TRADE_EXECUTED notification."""
        event = NotificationEvent(
            event_type=NotificationType.PAPER_TRADE_EXECUTED,
            title=f"Paper Trade Executed ({side}) — {symbol}",
            message=f"PaperBroker filled {side} order for {qty} {symbol} at ${price:,.2f}.",
            details={
                "symbol": symbol,
                "side": side,
                "quantity": f"{qty}",
                "price": f"${price:,.2f}",
                "fee": f"${fee:,.4f}",
            },
        )
        await self.notify(event)

    async def notify_trade_closed(
        self, symbol: str, qty: float, entry_price: float, exit_price: float, pnl: float
    ) -> None:
        """Send TRADE_CLOSED notification."""
        event = NotificationEvent(
            event_type=NotificationType.TRADE_CLOSED,
            title=f"Trade Closed — {symbol}",
            message=f"Position in {symbol} closed. Realized PnL: ${pnl:+,.2f}.",
            details={
                "symbol": symbol,
                "quantity": f"{qty}",
                "entry_price": f"${entry_price:,.2f}",
                "exit_price": f"${exit_price:,.2f}",
                "realized_pnl": f"${pnl:+,.2f}",
            },
        )
        await self.notify(event)

    async def notify_risk_rejection(self, symbol: str, reason: str) -> None:
        """Send RISK_REJECTION notification."""
        event = NotificationEvent(
            event_type=NotificationType.RISK_REJECTION,
            title=f"Order Rejected by Risk Engine — {symbol}",
            message=f"Proposed order for {symbol} was rejected by risk management.",
            details={"symbol": symbol, "reason": reason},
        )
        await self.notify(event)

    async def notify_market_data_failure(self, symbol: str, error: str) -> None:
        """Send MARKET_DATA_FAILURE notification."""
        event = NotificationEvent(
            event_type=NotificationType.MARKET_DATA_FAILURE,
            title=f"Market Data Error — {symbol}",
            message=f"Failed to fetch market data for {symbol}.",
            details={"symbol": symbol, "error": error},
        )
        await self.notify(event)

    async def notify_exchange_connection_failure(self, exchange: str, error: str) -> None:
        """Send EXCHANGE_CONNECTION_FAILURE notification."""
        event = NotificationEvent(
            event_type=NotificationType.EXCHANGE_CONNECTION_FAILURE,
            title=f"Exchange Connection Error — {exchange}",
            message=f"Connection failure communicating with {exchange}.",
            details={"exchange": exchange, "error": error},
        )
        await self.notify(event)

    async def notify_unexpected_exception(self, context: str, error: str) -> None:
        """Send UNEXPECTED_EXCEPTION notification."""
        event = NotificationEvent(
            event_type=NotificationType.UNEXPECTED_EXCEPTION,
            title="Unexpected System Exception",
            message=f"An unhandled exception occurred in {context}.",
            details={"context": context, "error": error},
        )
        await self.notify(event)

    async def notify_daily_loss_limit_reached(self, daily_loss_pct: float, threshold: float) -> None:
        """Send DAILY_LOSS_LIMIT_REACHED notification."""
        event = NotificationEvent(
            event_type=NotificationType.DAILY_LOSS_LIMIT_REACHED,
            title="Maximum Daily Loss Limit Reached",
            message=f"Trading halted: Daily loss ({daily_loss_pct:.2f}%) reached threshold ({threshold:.2f}%).",
            details={"daily_loss": f"{daily_loss_pct:.2f}%", "limit": f"{threshold:.2f}%"},
        )
        await self.notify(event)

    async def notify_emergency_stop(self, reason: str) -> None:
        """Send EMERGENCY_STOP notification."""
        event = NotificationEvent(
            event_type=NotificationType.EMERGENCY_STOP,
            title="EMERGENCY STOP TRIGGERED",
            message="Trading engine emergency stop activated. All trading halted.",
            details={"reason": reason},
        )
        await self.notify(event)

    async def close(self) -> None:
        """Close all registered notification providers."""
        for n in self.notifiers:
            try:
                await n.close()
            except Exception as e:
                logger.warning("notification_service.close_error", provider=n.name, error=str(e))
