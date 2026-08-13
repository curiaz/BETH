"""
BETHBot — Unit tests: Portfolio metrics.
"""

from datetime import datetime, timezone, timedelta

from app.engine.portfolio.metrics import PerformanceMetrics, compute_metrics


class TestComputeMetrics:
    def test_empty_equity_curve(self):
        metrics = compute_metrics([], [], 10000)
        assert metrics.total_return_pct == 0.0
        assert metrics.final_equity == 10000

    def test_positive_return(self):
        curve = [
            (datetime(2024, 1, 1, tzinfo=timezone.utc), 10000),
            (datetime(2024, 1, 2, tzinfo=timezone.utc), 10500),
            (datetime(2024, 1, 3, tzinfo=timezone.utc), 11000),
        ]
        metrics = compute_metrics(curve, [], 10000)
        assert metrics.total_return_pct == 10.0
        assert metrics.final_equity == 11000

    def test_negative_return(self):
        curve = [
            (datetime(2024, 1, 1, tzinfo=timezone.utc), 10000),
            (datetime(2024, 1, 2, tzinfo=timezone.utc), 9000),
        ]
        metrics = compute_metrics(curve, [], 10000)
        assert metrics.total_return_pct == -10.0

    def test_max_drawdown(self):
        curve = [
            (datetime(2024, 1, 1, tzinfo=timezone.utc), 10000),
            (datetime(2024, 1, 2, tzinfo=timezone.utc), 12000),
            (datetime(2024, 1, 3, tzinfo=timezone.utc), 9000),  # 25% drawdown from peak
            (datetime(2024, 1, 4, tzinfo=timezone.utc), 11000),
        ]
        metrics = compute_metrics(curve, [], 10000)
        assert metrics.max_drawdown_pct == 25.0

    def test_win_rate(self):
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 200},
            {"pnl": -30},
        ]
        curve = [(datetime(2024, 1, 1, tzinfo=timezone.utc), 10000)]
        metrics = compute_metrics(curve, trades, 10000)
        assert metrics.win_rate == 50.0
        assert metrics.total_trades == 4
        assert metrics.winning_trades == 2
        assert metrics.losing_trades == 2

    def test_profit_factor(self):
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 200},
        ]
        curve = [(datetime(2024, 1, 1, tzinfo=timezone.utc), 10000)]
        metrics = compute_metrics(curve, trades, 10000)
        assert metrics.profit_factor == 6.0  # 300 / 50

    def test_sharpe_ratio_computed(self):
        # Create a curve with enough data points
        curve = [
            (datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i), 10000 + i * 10)
            for i in range(100)
        ]
        metrics = compute_metrics(curve, [], 10000)
        assert metrics.sharpe_ratio is not None
