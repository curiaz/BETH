"""
BETHBot — Database Unit Tests for Candle Repository.

Tests all required database methods:
1. save_candles() and get_candles() for BTC/USDT
2. save_candles() and get_candles() for ETH/USDT
3. Duplicate candle prevention (unique constraint & deduplication)
4. get_latest_candle()
5. get_date_range()
6. MarketDataSyncService cache hit duplicate download avoidance
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Candle
from app.repositories.candle_repository import CandleRepository
from app.services.market_data_sync import MarketDataSyncService


class DummyTestProvider:
    """Dummy provider to track whether fetch_candles was called."""

    def __init__(self):
        self.fetch_count = 0

    async def fetch_candles(self, symbol, timeframe, start, end=None, limit=1000):
        self.fetch_count += 1
        end_time = end or (start + timedelta(hours=1))
        candles = []
        curr = start
        while curr <= end_time:
            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time=curr,
                    close_time=curr + timedelta(hours=1),
                    open=Decimal("42000.00"),
                    high=Decimal("42500.00"),
                    low=Decimal("41800.00"),
                    close=Decimal("42300.00"),
                    volume=Decimal("10.0"),
                )
            )
            curr += timedelta(hours=1)
        return candles


@pytest.mark.asyncio
class TestCandleRepository:
    async def test_save_and_get_btc_usdt_candles(self, db_session: AsyncSession):
        """Test saving and retrieving BTC/USDT candles."""
        repo = CandleRepository(db_session)
        now = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

        c1 = Candle(
            symbol="BTC/USDT",
            timeframe="1h",
            open_time=now,
            close_time=now + timedelta(hours=1),
            open=Decimal("42000.00"),
            high=Decimal("42500.00"),
            low=Decimal("41800.00"),
            close=Decimal("42300.00"),
            volume=Decimal("15.5"),
        )
        c2 = Candle(
            symbol="BTC/USDT",
            timeframe="1h",
            open_time=now + timedelta(hours=1),
            close_time=now + timedelta(hours=2),
            open=Decimal("42300.00"),
            high=Decimal("42800.00"),
            low=Decimal("42100.00"),
            close=Decimal("42600.00"),
            volume=Decimal("12.0"),
        )

        saved = await repo.save_candles([c1, c2])
        assert saved == 2

        fetched = await repo.get_candles("BTC/USDT", "1h")
        assert len(fetched) == 2
        assert fetched[0].symbol == "BTC/USDT"
        assert fetched[0].open == Decimal("42000.00")
        assert fetched[1].close == Decimal("42600.00")

    async def test_save_and_get_eth_usdt_candles(self, db_session: AsyncSession):
        """Test saving and retrieving ETH/USDT candles."""
        repo = CandleRepository(db_session)
        now = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

        eth_candle = Candle(
            symbol="ETH/USDT",
            timeframe="1h",
            open_time=now,
            close_time=now + timedelta(hours=1),
            open=Decimal("2200.00"),
            high=Decimal("2250.00"),
            low=Decimal("2190.00"),
            close=Decimal("2240.00"),
            volume=Decimal("100.0"),
        )

        saved = await repo.save_candles([eth_candle])
        assert saved == 1

        fetched = await repo.get_candles("ETH/USDT", "1h")
        assert len(fetched) == 1
        assert fetched[0].symbol == "ETH/USDT"
        assert fetched[0].close == Decimal("2240.00")

    async def test_prevent_duplicate_candles(self, db_session: AsyncSession):
        """Test that duplicate candles are not re-inserted."""
        repo = CandleRepository(db_session)
        now = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

        c1 = Candle(
            symbol="BTC/USDT",
            timeframe="1h",
            open_time=now,
            close_time=now + timedelta(hours=1),
            open=Decimal("42000.00"),
            high=Decimal("42500.00"),
            low=Decimal("41800.00"),
            close=Decimal("42300.00"),
            volume=Decimal("15.5"),
        )

        # First save
        count1 = await repo.save_candles([c1])
        assert count1 == 1

        # Second save with identical (symbol, timeframe, open_time)
        c1_dup = Candle(
            symbol="BTC/USDT",
            timeframe="1h",
            open_time=now,
            close_time=now + timedelta(hours=1),
            open=Decimal("42000.00"),
            high=Decimal("42500.00"),
            low=Decimal("41800.00"),
            close=Decimal("42300.00"),
            volume=Decimal("15.5"),
        )
        count2 = await repo.save_candles([c1_dup])
        assert count2 == 0  # 0 inserted

        # Check database count remains 1
        all_candles = await repo.get_candles("BTC/USDT", "1h")
        assert len(all_candles) == 1

    async def test_get_latest_candle(self, db_session: AsyncSession):
        """Test get_latest_candle retrieves the latest open_time candle."""
        repo = CandleRepository(db_session)
        t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        t1 = t0 + timedelta(hours=1)
        t2 = t0 + timedelta(hours=2)

        c1 = Candle(symbol="BTC/USDT", timeframe="1h", open_time=t0, close_time=t1, open=Decimal("40000"), high=Decimal("40500"), low=Decimal("39800"), close=Decimal("40200"), volume=Decimal("10"))
        c2 = Candle(symbol="BTC/USDT", timeframe="1h", open_time=t2, close_time=t2 + timedelta(hours=1), open=Decimal("40200"), high=Decimal("41000"), low=Decimal("40100"), close=Decimal("40900"), volume=Decimal("20"))

        await repo.save_candles([c1, c2])

        latest = await repo.get_latest_candle("BTC/USDT", "1h")
        assert latest is not None
        assert latest.open_time == t2
        assert latest.close == Decimal("40900")

    async def test_get_date_range(self, db_session: AsyncSession):
        """Test get_date_range returns (earliest, latest) open_time."""
        repo = CandleRepository(db_session)
        t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        t5 = t0 + timedelta(hours=5)

        c1 = Candle(symbol="BTC/USDT", timeframe="1h", open_time=t0, close_time=t0 + timedelta(hours=1), open=Decimal("40000"), high=Decimal("40500"), low=Decimal("39800"), close=Decimal("40200"), volume=Decimal("10"))
        c2 = Candle(symbol="BTC/USDT", timeframe="1h", open_time=t5, close_time=t5 + timedelta(hours=1), open=Decimal("40200"), high=Decimal("41000"), low=Decimal("40100"), close=Decimal("40900"), volume=Decimal("20"))

        await repo.save_candles([c1, c2])

        date_range = await repo.get_date_range("BTC/USDT", "1h")
        assert date_range is not None
        earliest, latest = date_range
        assert earliest == t0
        assert latest == t5

    async def test_market_data_sync_avoids_duplicate_download(self, db_session: AsyncSession):
        """Test that MarketDataSyncService avoids downloading data if cached."""
        repo = CandleRepository(db_session)
        provider = DummyTestProvider()
        sync_service = MarketDataSyncService(provider, repo)

        t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        t2 = t0 + timedelta(hours=2)

        # Initial sync: downloads from provider
        await sync_service.sync_candles("BTC/USDT", "1h", t0, t2)
        assert provider.fetch_count == 1

        # Second sync for same range: skips provider download!
        await sync_service.sync_candles("BTC/USDT", "1h", t0, t2)
        assert provider.fetch_count == 1  # Fetch count did not increase!
