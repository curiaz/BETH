# BETHBot

**B**TC **E**TH **T**rading **H**ub — A professional algorithmic trading platform.

## Overview

BETHBot is a personal algorithmic trading platform supporting BTC/USDT and ETH/USDT. It provides backtesting, paper trading, and (in future phases) live trading capabilities.

> ⚠️ **Phase 1**: The system operates exclusively in **backtest** and **paper-trading** mode. No real-money connections are implemented.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy (async) |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Data | Pandas, NumPy, pandas-ta |
| Frontend | Next.js, React, TypeScript, Tailwind CSS v4 |
| Infrastructure | Docker, GitHub Actions |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (optional, for PostgreSQL)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
copy .env.example .env        # Windows
# cp .env.example .env        # Linux/Mac

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup

```bash
docker compose up --build
```

### Run Tests

```bash
cd backend
pytest -v --cov=app
```

## Project Structure

```
BETHBot/
├── backend/          # Python trading engine + FastAPI
│   ├── app/
│   │   ├── core/     # Config, DB, logging, exceptions
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic request/response schemas
│   │   ├── api/      # FastAPI routers
│   │   ├── services/ # Business logic orchestration
│   │   ├── engine/   # Pure trading logic (strategy, risk, execution)
│   │   └── integrations/  # Exchange adapters, notifications
│   ├── tests/
│   └── alembic/      # Database migrations
├── frontend/         # Next.js trading dashboard
└── docker-compose.yml
```

## Configuration

All configuration is via environment variables (`.env` file). See `.env.example` for all options.

Key settings:
- `TRADING_MODE=paper` — Default mode. Set to `backtest` for backtesting.
- `PAPER_INITIAL_BALANCE=10000` — Starting capital in USDT.
- `SUPPORTED_SYMBOLS=BTC/USDT,ETH/USDT` — Comma-separated trading pairs.
- `DATABASE_URL` — SQLite for dev, PostgreSQL for production.

## License

Private — Personal use only.
