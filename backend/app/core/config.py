"""
BETHBot — Application configuration via pydantic-settings.

All configuration is loaded from environment variables and/or .env file.
Business logic NEVER reads .env directly — it receives typed values from this module.
"""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration. All values are configurable via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "BETHBot"
    app_env: str = Field(default="development", description="development | staging | production")
    trading_mode: str = Field(default="paper", description="backtest | paper")
    debug: bool = False

    # --- Exchange ---
    exchange: str = Field(default="binance", description="Exchange adapter to use")
    binance_api_key: str = ""
    binance_api_secret: str = ""

    # --- Trading ---
    paper_initial_balance: float = Field(
        default=10_000.0,
        description="Starting capital in USDT for paper trading / backtests",
    )
    supported_symbols: str = Field(
        default="BTC/USDT,ETH/USDT",
        description="Comma-separated trading pairs",
    )
    default_timeframe: str = Field(default="1h", description="Default OHLCV timeframe")

    # --- Database ---
    database_url: str = Field(
        default="sqlite+aiosqlite:///./bethbot.db",
        description="Async database URL (sqlite+aiosqlite or postgresql+asyncpg)",
    )
    database_echo: bool = False

    # --- Risk Defaults ---
    max_position_pct: float = Field(default=0.20, description="Max single position as % of equity")
    max_drawdown_pct: float = Field(default=0.15, description="Max drawdown before halt")
    max_daily_loss_pct: float = Field(default=0.03, description="Max daily loss as % of equity")
    max_exposure_pct: float = Field(default=0.80, description="Max total exposure as % of equity")

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated CORS origins",
    )

    # --- Notifications ---
    discord_webhook_url: str = ""

    # --- Logging ---
    log_level: str = "INFO"

    # --- Computed properties ---

    @property
    def symbols_list(self) -> list[str]:
        """Parse SUPPORTED_SYMBOLS into a list."""
        return [s.strip() for s in self.supported_symbols.split(",") if s.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @field_validator("trading_mode")
    @classmethod
    def validate_trading_mode(cls, v: str) -> str:
        allowed = {"backtest", "paper"}
        if v not in allowed:
            raise ValueError(
                f"trading_mode must be one of {allowed}. "
                f"Live trading is not supported in Phase 1."
            )
        return v

    def __repr__(self) -> str:
        return (
            f"<Settings app_env={self.app_env} trading_mode={self.trading_mode} "
            f"exchange={self.exchange} binance_api_key='****' binance_api_secret='****' "
            f"discord_webhook_url='****'>"
        )


# Singleton — import this everywhere
settings = Settings()
