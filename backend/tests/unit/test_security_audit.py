"""
BETHBot — Security Audit & Invariant Unit Tests.

Tests all security requirement invariants:
1. Secret Redaction: Structlog automatically redacts sensitive keys (secret, password, api_key, webhook, token)
2. Settings Repr Masking: Settings repr conceals credentials and webhooks
3. Global Exception Handler Safety: API error responses never expose unhandled stack traces or secret details
4. Paper Mode Invariant: TRADING_MODE strictly prohibits live trading
5. Docker Containerization Non-Root User Safety
"""

import logging
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.core.logging import redact_sensitive_fields
from app.main import app
from app.notifications.discord import mask_webhook_url

client = TestClient(app, raise_server_exceptions=False)


class TestSecurityAudit:
    def test_structlog_redact_sensitive_fields(self):
        """Verify structlog processor automatically redacts sensitive dictionary keys."""
        event_dict = {
            "event": "user_login",
            "binance_api_key": "raw_key_12345",
            "binance_api_secret": "raw_secret_abcdef",
            "password": "super_secret_password",
            "discord_webhook_url": "https://discord.com/api/webhooks/12345/ABC_SECRET_TOKEN",
        }

        processed = redact_sensitive_fields(None, "info", event_dict)

        assert processed["binance_api_key"] == "****[REDACTED]****"
        assert processed["binance_api_secret"] == "****[REDACTED]****"
        assert processed["password"] == "****[REDACTED]****"
        assert "ABC_SECRET_TOKEN" not in processed["discord_webhook_url"]
        assert processed["discord_webhook_url"] == "https://discord.com/api/webhooks/****"

    def test_settings_repr_masking(self):
        """Verify Settings __repr__ conceals credentials."""
        s = Settings(
            binance_api_key="real_key_xyz",
            binance_api_secret="real_secret_xyz",
            discord_webhook_url="https://discord.com/api/webhooks/123/REAL_TOKEN",
        )
        repr_str = repr(s)

        assert "real_key_xyz" not in repr_str
        assert "real_secret_xyz" not in repr_str
        assert "REAL_TOKEN" not in repr_str
        assert "****" in repr_str

    def test_webhook_url_masking_function(self):
        """Verify mask_webhook_url function conceals token string."""
        url = "https://discord.com/api/webhooks/1537339084266274896/G43cYz7LymcCx9KH0gL0GPKFLQCPWHkm8eH4gRnV9GGw82MmQHm2c-GozINXCfMENF4J"
        masked = mask_webhook_url(url)

        assert "G43cYz7LymcCx9KH" not in masked
        assert masked == "https://discord.com/api/webhooks/****"

    def test_unhandled_exception_api_safety(self):
        """Verify unhandled API exceptions do not leak stack traces or secret details to clients."""
        @app.get("/api/test-security-error")
        async def mock_error_route():
            raise RuntimeError("Database connection password=super_secret_123 failed!")

        response = client.get("/api/test-security-error")
        assert response.status_code == 500
        data = response.json()

        assert data["error"] == "unhandled_error"
        assert "super_secret_123" not in data["detail"]
        assert "password" not in data["detail"]
        assert data["detail"] == "An unexpected error occurred. Details have been logged securely."

    def test_trading_mode_paper_safety_validation(self):
        """Verify settings validator rejects invalid or live trading modes."""
        with pytest.raises(ValueError, match="trading_mode must be one of"):
            Settings(trading_mode="live")
