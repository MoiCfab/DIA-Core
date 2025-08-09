from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Mode = Literal["dry_run", "paper", "live"]


class ExchangeMeta(BaseModel):
    symbol: str = Field(..., description="Paire ex: 'BTC/EUR'")
    price_decimals: int = 2
    qty_decimals: int = 6
    min_qty: float = 0.0001
    min_notional: float = 10.0


class RiskLimits(BaseModel):
    max_daily_loss_pct: float = 2.0
    max_drawdown_pct: float = 15.0
    max_exposure_pct: float = 50.0
    risk_per_trade_pct: float = 0.5
    max_orders_per_min: int = 30


class AppConfig(BaseModel):
    mode: Mode = "dry_run"
    exchange: ExchangeMeta
    risk: RiskLimits = RiskLimits()
    data_window_bars: int = 1000
    cache_dir: str = "state/cache"
    journal_path: str = "state/journal.sqlite"
    log_dir: str = "logs"
    pair: str = "XXBTZEUR"
    require_interactive_confirm: bool = True

    @field_validator("mode")
    @classmethod
    def warn_if_live(cls, v: Mode) -> Mode:
        if v == "live":
            print("[SECURITY] Attention: mode LIVE activé")
        return v
