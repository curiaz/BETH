"""
BETHBot — Unit Tests for Performance Analytics & Backtest Reports.

Tests all required calculations:
1. Starting balance, Ending balance, Net P/L, Total return
2. Strategy performance vs Market performance (Buy & Hold) distinction & Alpha
3. Number of trades, Winning trades, Losing trades, Win rate %
4. Average trade PnL, Average winning trade PnL, Average losing trade PnL
5. Profit factor calculation
6. Maximum drawdown calculation
7. Sharpe ratio calculation (when statistically appropriate)
8. Independent BacktestReport generation for BTC/USDT and ETH/USDT
9. AssetComparisonReport between BTC/USDT and ETH/USDT
10. Non-profitability disclaimer verification
"""

from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
import pytest

from app.domain.models import BacktestResultDomain
from app.engine.portfolio.analytics import (
    AssetComparisonReport,
    BacktestReport,
    PerformanceAnalytics,
)


class TestPerformanceAnalytics:
    def test_basic_balance_and_return_calculations(self):
        """Test starting balance, ending balance, net PnL, total return."""
        equity_curve = [
            (datetime(2024, 1, 1, tzinfo=timezone.utc), 10000.0),
            (datetime(2024, 1, 2, tzinfo=timezone.utc), 11000.0),
            (datetime(2024, 1, 3, tzinfo=timezone.utc), 12500.0),
        ]
        trades = [
            {"pnl": 1000.0},
            {"pnl": 1500.0},
        ]

        metrics = PerformanceAnalytics.calculate_analytics(
            starting_balance=10000.0,
            equity_curve=equity_curve,
            trades=trades,
        )

        assert metrics["starting_balance"] == Decimal("10000.0")
        assert metrics["ending_balance"] == Decimal("12500.0")
        assert metrics["net_pnl"] == Decimal("2500.0")
        assert metrics["total_return_pct"] == 25.0

    def test_strategy_vs_market_performance_distinction(self):
        """Test distinguishing strategy performance from market Buy & Hold return."""
        equity_curve = [
            (datetime(2024, 1, 1, tzinfo=timezone.utc), 10000.0),
            (datetime(2024, 1, 2, tzinfo=timezone.utc), 12000.0),  # +20% strategy return
        ]
        trades = [{"pnl": 2000.0}]

        # Market prices: 40000 -> 44000 (+10% market return)
        market_candles = pd.DataFrame(
            {"close": [40000.0, 44000.0]},
            index=[datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 2, tzinfo=timezone.utc)],
        )

        metrics = PerformanceAnalytics.calculate_analytics(
            starting_balance=10000.0,
            equity_curve=equity_curve,
            trades=trades,
            market_candles=market_candles,
        )

        assert metrics["total_return_pct"] == 20.0
        assert metrics["market_return_pct"] == 10.0
        assert metrics["strategy_alpha_pct"] == 10.0  # 20.0 - 10.0

    def test_trade_averages_and_win_rate(self):
        """Test trade count, win/loss counts, win rate, avg win, avg loss, profit factor."""
        trades = [
            {"realized_pnl": 300.0},
            {"realized_pnl": -100.0},
            {"realized_pnl": 500.0},
            {"realized_pnl": -100.0},
        ]
        equity_curve = [(datetime(2024, 1, 1, tzinfo=timezone.utc), 10000.0)]

        metrics = PerformanceAnalytics.calculate_analytics(
            starting_balance=10000.0,
            equity_curve=equity_curve,
            trades=trades,
        )

        assert metrics["total_trades"] == 4
        assert metrics["winning_trades"] == 2
        assert metrics["losing_trades"] == 2
        assert metrics["win_rate_pct"] == 50.0

        assert metrics["avg_trade_pnl"] == 150.0  # (300 - 100 + 500 - 100) / 4
        assert metrics["avg_winning_trade_pnl"] == 400.0  # (300 + 500) / 2
        assert metrics["avg_losing_trade_pnl"] == -100.0  # (-100 - 100) / 2
        assert metrics["profit_factor"] == 4.0  # 800 / 200

    def test_max_drawdown(self):
        """Test max drawdown calculation."""
        equity_curve = [
            {"equity": 10000.0},
            {"equity": 12000.0},  # Peak
            {"equity": 9000.0},   # 25% decline from 12000
            {"equity": 11000.0},
        ]

        metrics = PerformanceAnalytics.calculate_analytics(
            starting_balance=10000.0,
            equity_curve=equity_curve,
            trades=[],
        )

        assert metrics["max_drawdown_pct"] == 25.0

    def test_sharpe_ratio_statistical_appropriateness(self):
        """Test Sharpe ratio calculation when sample size >= 2 and std > 0."""
        equity_curve = [
            {"equity": 10000.0 + i * 50} for i in range(50)
        ]

        metrics = PerformanceAnalytics.calculate_analytics(
            starting_balance=10000.0,
            equity_curve=equity_curve,
            trades=[],
        )

        assert metrics["sharpe_ratio"] is not None
        assert metrics["sharpe_ratio"] > 0

    def test_independent_btc_and_eth_reports(self):
        """Test generating BacktestReport independently for BTC/USDT and ETH/USDT."""
        now = datetime.now(timezone.utc)

        btc_res = BacktestResultDomain(
            strategy_name="sma_crossover",
            symbol="BTC/USDT",
            timeframe="1h",
            start_date=now,
            end_date=now,
            initial_capital=Decimal("10000.0"),
            final_equity=Decimal("11500.0"),
            equity_curve=[{"equity": 10000.0}, {"equity": 11500.0}],
            trade_log=[{"realized_pnl": 1500.0}],
        )

        eth_res = BacktestResultDomain(
            strategy_name="sma_crossover",
            symbol="ETH/USDT",
            timeframe="1h",
            start_date=now,
            end_date=now,
            initial_capital=Decimal("10000.0"),
            final_equity=Decimal("12200.0"),
            equity_curve=[{"equity": 10000.0}, {"equity": 12200.0}],
            trade_log=[{"realized_pnl": 2200.0}],
        )

        report_btc = PerformanceAnalytics.generate_report(btc_res)
        report_eth = PerformanceAnalytics.generate_report(eth_res)

        assert report_btc.symbol == "BTC/USDT"
        assert report_btc.total_return_pct == 15.0
        assert "NOT guarantee" in report_btc.disclaimer

        assert report_eth.symbol == "ETH/USDT"
        assert report_eth.total_return_pct == 22.0
        assert "NOT guarantee" in report_eth.disclaimer

    def test_asset_comparison_report(self):
        """Test generating AssetComparisonReport comparing BTC/USDT and ETH/USDT."""
        now = datetime.now(timezone.utc)

        btc_res = BacktestResultDomain(
            strategy_name="sma_crossover",
            symbol="BTC/USDT",
            timeframe="1h",
            start_date=now,
            end_date=now,
            initial_capital=Decimal("10000.0"),
            final_equity=Decimal("11500.0"),
            equity_curve=[{"equity": 10000.0}, {"equity": 11500.0}],
            trade_log=[{"realized_pnl": 1500.0}],
        )

        eth_res = BacktestResultDomain(
            strategy_name="sma_crossover",
            symbol="ETH/USDT",
            timeframe="1h",
            start_date=now,
            end_date=now,
            initial_capital=Decimal("10000.0"),
            final_equity=Decimal("12200.0"),
            equity_curve=[{"equity": 10000.0}, {"equity": 12200.0}],
            trade_log=[{"realized_pnl": 2200.0}],
        )

        report_btc = PerformanceAnalytics.generate_report(btc_res)
        report_eth = PerformanceAnalytics.generate_report(eth_res)

        comp_report = PerformanceAnalytics.generate_comparison_report([report_btc, report_eth])

        assert isinstance(comp_report, AssetComparisonReport)
        assert len(comp_report.summary_table) == 2
        assert comp_report.best_returning_asset == "ETH/USDT"
        assert "NOT guarantee" in comp_report.disclaimer
