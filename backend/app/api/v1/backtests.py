"""
BETHBot — Backtest endpoints.
"""

from __future__ import annotations

import json
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import select

from app.core.config import settings
from app.core.dependencies import DBSession
from app.models.asset import Asset
from app.models.backtest_result import BacktestResult
from app.schemas.backtest import BacktestRequest, BacktestResultResponse
from app.services.backtester import BacktestService

router = APIRouter()


@router.post("", response_model=dict)
async def run_backtest(request: BacktestRequest, session: DBSession) -> dict:
    """Launch a backtest run."""
    # Get candle data from DB
    from app.services.market_data import MarketDataService
    from app.integrations.exchange.binance import BinanceAdapter

    # Try to load from DB first
    from app.models.candle import Candle
    result = await session.execute(select(Asset).where(Asset.symbol == request.symbol))
    asset = result.scalar_one_or_none()

    if not asset:
        return {"error": f"Asset {request.symbol} not found. Seed the database first."}

    query = (
        select(Candle)
        .where(
            Candle.asset_id == asset.id,
            Candle.timeframe == request.timeframe,
            Candle.open_time >= request.start_date,
            Candle.open_time <= request.end_date,
        )
        .order_by(Candle.open_time)
    )
    candle_result = await session.execute(query)
    candles = candle_result.scalars().all()

    if not candles:
        return {
            "error": "No candle data available for the specified range. "
                     "Fetch market data first using the market data endpoints."
        }

    import pandas as pd
    records = [
        {
            "open_time": c.open_time,
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume),
        }
        for c in candles
    ]
    df = pd.DataFrame(records)
    df.set_index("open_time", inplace=True)

    # Run backtest
    service = BacktestService()
    result = await service.run(
        strategy_name=request.strategy_name,
        parameters=request.parameters,
        data=df,
        symbol=request.symbol,
        initial_capital=request.initial_capital,
        slippage_pct=request.slippage_pct,
        fee_pct=request.fee_pct,
    )

    # Save result to DB
    bt_result = BacktestResult(
        strategy_name=request.strategy_name,
        parameters_json=json.dumps(request.parameters),
        asset_id=asset.id,
        timeframe=request.timeframe,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=Decimal(str(request.initial_capital)),
        final_equity=Decimal(str(result["final_equity"])),
        total_return_pct=result["total_return_pct"],
        sharpe_ratio=result.get("sharpe_ratio"),
        sortino_ratio=result.get("sortino_ratio"),
        max_drawdown_pct=result["max_drawdown_pct"],
        win_rate=result["win_rate"],
        total_trades=result["total_trades"],
        profit_factor=result.get("profit_factor"),
        equity_curve_json=json.dumps(result.get("equity_curve", [])),
        trade_log_json=json.dumps(result.get("trade_log", [])),
    )
    session.add(bt_result)
    await session.flush()

    return result


@router.get("", response_model=list[dict])
async def list_backtests(session: DBSession) -> list[dict]:
    """List all backtest runs."""
    result = await session.execute(
        select(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(50)
    )
    backtests = result.scalars().all()
    return [
        {
            "id": bt.id,
            "strategy_name": bt.strategy_name,
            "timeframe": bt.timeframe,
            "total_return_pct": bt.total_return_pct,
            "sharpe_ratio": bt.sharpe_ratio,
            "max_drawdown_pct": bt.max_drawdown_pct,
            "total_trades": bt.total_trades,
            "win_rate": bt.win_rate,
            "created_at": bt.created_at.isoformat() if bt.created_at else None,
        }
        for bt in backtests
    ]


@router.get("/{backtest_id}")
async def get_backtest(backtest_id: int, session: DBSession) -> dict:
    """Get detailed backtest results."""
    result = await session.execute(
        select(BacktestResult).where(BacktestResult.id == backtest_id)
    )
    bt = result.scalar_one_or_none()
    if not bt:
        return {"error": "Backtest not found"}

    return {
        "id": bt.id,
        "strategy_name": bt.strategy_name,
        "parameters": json.loads(bt.parameters_json) if bt.parameters_json else {},
        "timeframe": bt.timeframe,
        "initial_capital": float(bt.initial_capital),
        "final_equity": float(bt.final_equity),
        "total_return_pct": bt.total_return_pct,
        "sharpe_ratio": bt.sharpe_ratio,
        "sortino_ratio": bt.sortino_ratio,
        "max_drawdown_pct": bt.max_drawdown_pct,
        "win_rate": bt.win_rate,
        "total_trades": bt.total_trades,
        "profit_factor": bt.profit_factor,
        "equity_curve": json.loads(bt.equity_curve_json) if bt.equity_curve_json else [],
        "trade_log": json.loads(bt.trade_log_json) if bt.trade_log_json else [],
        "created_at": bt.created_at.isoformat() if bt.created_at else None,
    }
