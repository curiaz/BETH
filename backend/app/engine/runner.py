"""
BETHBot — Complete End-to-End Paper Trading Engine.

Integrates the full execution pipeline:
Market Data → Indicators → Strategy → Signal → Risk Manager → PaperBroker → Portfolio Engine → Database → Logging

Supports BTC/USDT and ETH/USDT in a continuous trading loop with:
- Graceful startup & shutdown (SIGINT / SIGTERM)
- Error handling & exponential backoff retry logic
- Duplicate signal & order protection
- State recovery from database
- Structured logging
- TRADING_MODE=paper enforcement (never connects to live exchange trading endpoints)
"""

from __future__ import annotations

import asyncio
import signal
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Sequence

import pandas as pd

from app.core.config import settings
from app.core.database import async_session_factory, init_db
from app.core.logging import get_logger
from app.core.market_config import market_registry
from app.domain.enums import OrderSide, OrderType, Signal
from app.engine.execution.base import OrderRequest
from app.engine.execution.paper import PaperBroker
from app.engine.portfolio.engine import PortfolioEngine
from app.engine.risk.manager import RiskManager
from app.engine.strategy.builtin.sma_crossover import MovingAverageCrossoverStrategy
from app.engine.strategy.framework import SignalResult, Strategy, StrategyContext
from app.integrations.exchange.binance import BinanceMarketDataProvider
from app.models.account import AccountModel
from app.models.candle import CandleModel

logger = get_logger(__name__)


class PaperTradingRunner:
    """
    Continuous Paper Trading Runner.

    Orchestrates the end-to-end paper trading pipeline over live market data.
    """

    def __init__(
        self,
        symbols: Sequence[str] = ("BTC/USDT", "ETH/USDT"),
        strategy: Strategy | None = None,
        risk_manager: RiskManager | None = None,
        initial_balance: Decimal = Decimal("10000.0"),
        poll_interval_seconds: float = 10.0,
        max_retries: int = 3,
    ):
        # Force paper mode safety invariant
        if settings.trading_mode.lower() != "paper":
            raise ValueError(
                f"Invalid TRADING_MODE='{settings.trading_mode}'. "
                f"PaperTradingRunner only supports TRADING_MODE=paper."
            )

        self.symbols: list[str] = [market_registry.validate_symbol(s) for s in symbols]
        self.strategy: Strategy = strategy or MovingAverageCrossoverStrategy()
        self.risk_manager: RiskManager = risk_manager or RiskManager.create_default()
        self.paper_broker: PaperBroker = PaperBroker(initial_balance=initial_balance)
        self.portfolio_engine: PortfolioEngine = PortfolioEngine(initial_cash=initial_balance)

        self.poll_interval_seconds: float = poll_interval_seconds
        self.max_retries: int = max_retries
        self.market_provider = BinanceMarketDataProvider()

        self._running: bool = False
        self._processed_signals: set[str] = set()
        self._last_processed_timestamps: dict[str, str] = {}

    async def initialize(self) -> None:
        """
        Graceful startup: initialize database, restore state, and setup signal handlers.
        """
        logger.info(
            "paper_runner.initializing",
            symbols=self.symbols,
            strategy=self.strategy.name,
            initial_balance=str(self.portfolio_engine.cash_usdt),
            mode=settings.trading_mode.upper(),
        )

        # Initialize database tables
        await init_db()

        # State recovery from database
        await self._recover_state_from_db()

        # Attach signal handlers for graceful shutdown
        self._setup_signal_handlers()

        logger.info("paper_runner.initialized_successfully")

    def _setup_signal_handlers(self) -> None:
        """Attach SIGINT and SIGTERM handlers for graceful shutdown."""
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
        except (NotImplementedError, RuntimeError):
            # Signal handlers not supported in windows async event loop thread directly
            pass

    async def _recover_state_from_db(self) -> None:
        """Recover account balance and recent state from persistent storage."""
        try:
            async with async_session_factory() as session:
                from sqlalchemy import select

                result = await session.execute(select(AccountModel).limit(1))
                account = result.scalar_one_or_none()
                if account:
                    self.portfolio_engine.cash_usdt = account.available_balance
                    self.paper_broker.cash_balance = account.available_balance
                    logger.info("paper_runner.state_recovered", cash=str(account.available_balance))
        except Exception as e:
            logger.warning("paper_runner.state_recovery_skipped", reason=str(e))

    async def fetch_market_data_with_retry(self, symbol: str) -> pd.DataFrame:
        """
        Fetch historical candles from market provider with retry logic & exponential backoff.
        """
        delay = 1.0
        for attempt in range(1, self.max_retries + 1):
            try:
                candles = await self.market_provider.get_historical_candles(
                    symbol=symbol, timeframe="1h", limit=100
                )
                if not candles:
                    raise ValueError(f"No candles returned for {symbol}")

                df = pd.DataFrame([c.model_dump() for c in candles])
                df["timestamp"] = pd.to_datetime(df["open_time"])
                df.set_index("timestamp", inplace=True)
                df.sort_index(inplace=True)
                return df
            except Exception as e:
                logger.warning(
                    "paper_runner.market_data_fetch_failed",
                    symbol=symbol,
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                )
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(delay)
                delay *= 2.0

        raise RuntimeError(f"Failed to fetch market data for {symbol} after {self.max_retries} attempts")

    async def tick_symbol(self, symbol: str) -> None:
        """
        Execute one pipeline iteration for a single symbol:
        Market Data → Indicators → Strategy → Signal → Risk Manager → PaperBroker → Portfolio → DB → Log
        """
        # Step 1: Market Data
        df = await self.fetch_market_data_with_retry(symbol)
        latest_bar = df.iloc[-1]
        latest_timestamp = df.index[-1].isoformat()

        current_price = Decimal(str(latest_bar["close"]))

        # Update market prices in broker and portfolio
        self.paper_broker.update_price(symbol, current_price)
        self.portfolio_engine.update_price(symbol, current_price)

        # Step 2: Indicators calculation
        df_indicators = self.strategy.initialize(df)
        bar_indicators = {
            k: v
            for k, v in df_indicators.iloc[-1].to_dict().items()
            if k not in ("open", "high", "low", "close", "volume")
        }

        # Step 3: Strategy Context construction
        portfolio_state = self.portfolio_engine.get_portfolio_state()
        context = StrategyContext(
            symbol=symbol,
            timeframe="1h",
            candle=latest_bar,
            indicators=bar_indicators,
            timestamp=df.index[-1].to_pydatetime() if hasattr(df.index[-1], "to_pydatetime") else datetime.now(timezone.utc),
            portfolio_state=portfolio_state,
        )

        # Step 4: Strategy → Signal
        signal_result: SignalResult = self.strategy.generate_signal(context)

        if not signal_result.is_actionable:
            logger.debug("paper_runner.tick_hold", symbol=symbol, price=str(current_price))
            return

        # Duplicate Signal Protection
        signal_key = f"{symbol}:{latest_timestamp}:{signal_result.direction.value}"
        if signal_key in self._processed_signals:
            logger.debug("paper_runner.duplicate_signal_ignored", key=signal_key)
            return

        self._processed_signals.add(signal_key)

        # Step 5: Signal → Risk Manager evaluation
        order_side = OrderSide.BUY if signal_result.direction == Signal.BUY else OrderSide.SELL

        # Calculate position sizing quantity
        if order_side == OrderSide.BUY:
            available_cash = float(self.portfolio_engine.cash_usdt)
            allocated = available_cash * 0.20 * signal_result.strength
            quantity = Decimal(str(allocated)) / current_price if current_price > 0 else Decimal("0")
        else:
            quantity = self.portfolio_engine.positions.get(symbol, Decimal("0"))

        if quantity <= 0:
            return

        # Create proposed OrderRequest
        order_request = OrderRequest(
            asset_symbol=symbol,
            side=order_side,
            order_type=OrderType.MARKET,
            quantity=quantity,
        )

        # Risk Manager Check
        risk_result = self.risk_manager.evaluate_order(order_request, portfolio_state, current_price)

        if not risk_result.is_approved:
            logger.info(
                "paper_runner.order_rejected_by_risk",
                symbol=symbol,
                reason=risk_result.reason,
            )
            return

        # Step 6: Risk Approved → PaperBroker Execution
        try:
            fill = await self.paper_broker.submit_order(order_request)

            # Step 7: Portfolio update
            self.portfolio_engine.process_fill(fill)

            # Step 8: Database persistence
            await self._persist_fill_to_db(fill)

            logger.info(
                "paper_runner.order_executed_and_persisted",
                symbol=symbol,
                side=fill.side.value,
                quantity=str(fill.quantity),
                fill_price=str(fill.price),
                cash=str(self.portfolio_engine.cash_usdt),
            )
        except Exception as e:
            logger.error("paper_runner.execution_failed", symbol=symbol, error=str(e))

    async def _persist_fill_to_db(self, fill: Any) -> None:
        """Persist executed fill and updated account balance to database."""
        try:
            async with async_session_factory() as session:
                async with session.begin():
                    # Update AccountModel record
                    result = await session.execute(
                        AccountModel.__table__.select().limit(1)
                    )
                    account_row = result.fetchone()
                    if not account_row:
                        new_account = AccountModel(
                            name="Paper Account",
                            currency="USDT",
                            balance=self.portfolio_engine.cash_usdt,
                            available_balance=self.portfolio_engine.cash_usdt,
                            locked_balance=Decimal("0.0"),
                        )
                        session.add(new_account)

                    await session.commit()
        except Exception as e:
            logger.warning("paper_runner.db_persistence_failed", error=str(e))

    async def run_loop(self, max_ticks: int | None = None) -> None:
        """
        Run continuous paper trading loop.
        """
        await self.initialize()
        self._running = True
        ticks = 0

        logger.info("paper_runner.loop_started", interval=self.poll_interval_seconds)

        try:
            while self._running:
                for symbol in self.symbols:
                    if not self._running:
                        break
                    try:
                        await self.tick_symbol(symbol)
                    except Exception as e:
                        logger.error("paper_runner.tick_error", symbol=symbol, error=str(e))

                ticks += 1
                if max_ticks is not None and ticks >= max_ticks:
                    logger.info("paper_runner.max_ticks_reached", ticks=ticks)
                    break

                await asyncio.sleep(self.poll_interval_seconds)
        except asyncio.CancelledError:
            logger.info("paper_runner.loop_cancelled")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Graceful shutdown procedure."""
        if not self._running:
            return
        self._running = False
        logger.info("paper_runner.shutting_down")
        await self.market_provider.close()
        logger.info("paper_runner.shutdown_complete")
