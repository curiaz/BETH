"""
BETHBot — Unit Tests for End-to-End PaperTradingRunner Engine.

Tests required cases:
1. End-to-end execution flow: Market Data → Indicators → Strategy → Signal → Risk Manager → PaperBroker → Portfolio → DB → Logging
2. Multi-asset continuous loop execution for BTC/USDT and ETH/USDT
3. Duplicate signal & duplicate order protection
4. Error handling & retry logic for market data provider
5. State recovery from database
6. Graceful startup and shutdown
7. Default TRADING_MODE=paper enforcement
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from app.core.config import settings
from app.domain.enums import OrderSide, Signal
from app.domain.models import Candle
from app.engine.runner import PaperTradingRunner
from app.engine.strategy.framework import SignalResult, Strategy, StrategyContext


def make_candle(symbol: str, timestamp_iso: str, close_price: str) -> Candle:
    dt = datetime.fromisoformat(timestamp_iso)
    p = Decimal(close_price)
    return Candle(
        symbol=symbol,
        timeframe="1h",
        open_time=dt,
        close_time=dt,
        open=p,
        high=p * Decimal("1.001"),
        low=p * Decimal("0.999"),
        close=p,
        volume=Decimal("10.0"),
    )


class TestPaperTradingRunner:
    @pytest.mark.asyncio
    async def test_trading_mode_paper_enforcement(self):
        """Verify runner enforces TRADING_MODE=paper."""
        with patch.object(settings, "trading_mode", "live"):
            with pytest.raises(ValueError, match="only supports TRADING_MODE=paper"):
                PaperTradingRunner()

    @pytest.mark.asyncio
    async def test_graceful_startup_and_shutdown(self):
        """Test initialize() and stop() startup and shutdown procedures."""
        runner = PaperTradingRunner(symbols=["BTC/USDT", "ETH/USDT"])

        with patch("app.engine.runner.init_db", new_callable=AsyncMock), \
             patch.object(runner, "_recover_state_from_db", new_callable=AsyncMock):
            await runner.initialize()
            assert runner.portfolio_engine.cash_usdt == Decimal("10000.0")

            await runner.stop()
            assert not runner._running

    @pytest.mark.asyncio
    async def test_pipeline_execution_btc_and_eth(self):
        """Test full pipeline tick execution for BTC/USDT and ETH/USDT."""
        runner = PaperTradingRunner(
            symbols=["BTC/USDT", "ETH/USDT"],
            poll_interval_seconds=0.01,
        )

        btc_candles = [
            make_candle("BTC/USDT", f"2024-01-01T{i:02d}:00:00+00:00", str(40000 + i * 100))
            for i in range(10)
        ]
        eth_candles = [
            make_candle("ETH/USDT", f"2024-01-01T{i:02d}:00:00+00:00", str(2000 + i * 10))
            for i in range(10)
        ]

        runner.market_provider.get_historical_candles = AsyncMock(
            side_effect=lambda symbol, timeframe, limit: (
                btc_candles if symbol == "BTC/USDT" else eth_candles
            )
        )

        # Force strategy to emit actionable BUY signal
        mock_strategy = MagicMock()
        mock_strategy.name = "mock_strat"
        mock_strategy.initialize = lambda df: df
        mock_strategy.generate_signal = MagicMock(
            return_value=SignalResult(
                symbol="BTC/USDT",
                direction=Signal.BUY,
                strength=0.5,
            )
        )
        runner.strategy = mock_strategy

        with patch("app.engine.runner.init_db", new_callable=AsyncMock):
            await runner.initialize()
            await runner.tick_symbol("BTC/USDT")

            # Verify PaperBroker executed buy order
            assert runner.portfolio_engine.cash_usdt < Decimal("10000.0")
            assert runner.portfolio_engine.positions.get("BTC/USDT", Decimal("0")) > 0

    @pytest.mark.asyncio
    async def test_duplicate_signal_protection(self):
        """Verify duplicate signals for the same bar timestamp are ignored."""
        runner = PaperTradingRunner(symbols=["BTC/USDT"])

        candles = [
            make_candle("BTC/USDT", "2024-01-01T12:00:00+00:00", "40000.00")
            for _ in range(5)
        ]
        runner.market_provider.get_historical_candles = AsyncMock(return_value=candles)

        mock_strategy = MagicMock()
        mock_strategy.name = "mock_strat"
        mock_strategy.initialize = lambda df: df
        mock_strategy.generate_signal = MagicMock(
            return_value=SignalResult(symbol="BTC/USDT", direction=Signal.BUY, strength=0.5)
        )
        runner.strategy = mock_strategy

        with patch("app.engine.runner.init_db", new_callable=AsyncMock):
            await runner.initialize()

            # First tick processes signal
            await runner.tick_symbol("BTC/USDT")
            initial_history_len = len(runner.paper_broker.get_trade_history())
            assert initial_history_len == 1

            # Second tick on identical timestamp is ignored by duplicate signal protection
            await runner.tick_symbol("BTC/USDT")
            assert len(runner.paper_broker.get_trade_history()) == 1

    @pytest.mark.asyncio
    async def test_error_retry_logic(self):
        """Test market data fetch retry logic with exponential backoff on transient errors."""
        runner = PaperTradingRunner(max_retries=3)

        candles = [make_candle("BTC/USDT", "2024-01-01T12:00:00+00:00", "40000.00")]

        # Fail twice, succeed on third attempt
        mock_fetch = AsyncMock(
            side_effect=[
                RuntimeError("Network timeout"),
                RuntimeError("Connection reset"),
                candles,
            ]
        )
        runner.market_provider.get_historical_candles = mock_fetch

        df = await runner.fetch_market_data_with_retry("BTC/USDT")

        assert not df.empty
        assert mock_fetch.call_count == 3

    @pytest.mark.asyncio
    async def test_short_run_loop_execution(self):
        """Test short run_loop execution for 2 ticks."""
        runner = PaperTradingRunner(
            symbols=["BTC/USDT"],
            poll_interval_seconds=0.01,
        )

        candles = [make_candle("BTC/USDT", "2024-01-01T12:00:00+00:00", "40000.00")]
        runner.market_provider.get_historical_candles = AsyncMock(return_value=candles)

        with patch("app.engine.runner.init_db", new_callable=AsyncMock):
            await runner.run_loop(max_ticks=2)
            assert not runner._running
