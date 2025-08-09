from __future__ import annotations

from pydantic import BaseModel


class Position(BaseModel):
    symbol: str
    qty: float
    avg_price: float
    side: str  # "long" ou "short"
    unrealized_pnl: float = 0.0


class PortfolioSnapshot(BaseModel):
    equity: float
    cash: float
    positions: list[Position] = []
    max_drawdown_pct: float = 0.0
    exposure_pct: float = 0.0
