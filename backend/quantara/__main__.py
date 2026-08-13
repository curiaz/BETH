"""
Quantara CLI Entry Point.

Executable via:
  python -m quantara

Runs BETHBot's continuous paper-trading engine with graceful startup, shutdown, and logging.
"""

import argparse
import asyncio
import sys

from app.core.config import settings
from app.core.logging import get_logger
from app.engine.runner import PaperTradingRunner

logger = get_logger("quantara.cli")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m quantara",
        description="Quantara (BETHBot) Algorithmic Paper Trading Engine CLI",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default="BTC/USDT,ETH/USDT",
        help="Comma-separated symbols to trade (default: BTC/USDT,ETH/USDT)",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=None,
        help="Maximum tick iterations to run before exiting (default: infinite continuous loop)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=10.0,
        help="Polling interval in seconds between tick iterations (default: 10.0)",
    )
    return parser.parse_args()


async def main_async() -> None:
    args = parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    print("==========================================================================")
    print(f"               QUANTARA (BETHBot) PAPER TRADING ENGINE                    ")
    print(f" Mode:           TRADING_MODE={settings.trading_mode.upper()}            ")
    print(f" Symbols:        {symbols}                                                ")
    print(f" Capital:        {settings.paper_initial_balance} USDT                    ")
    print("==========================================================================")

    runner = PaperTradingRunner(
        symbols=symbols,
        poll_interval_seconds=args.interval,
    )

    try:
        await runner.run_loop(max_ticks=args.ticks)
    except KeyboardInterrupt:
        logger.info("quantara.cli_keyboard_interrupt")
        await runner.stop()
    except Exception as e:
        logger.error("quantara.cli_error", error=str(e))
        await runner.stop()
        sys.exit(1)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
