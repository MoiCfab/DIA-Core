from __future__ import annotations
from pydantic import BaseModel

class RiskLimits(BaseModel):
    max_daily_loss_pct: float = 2.0
    max_drawdown_pct: float = 15.0
    max_exposure_pct: float = 50.0
    risk_per_trade_pct: float = 0.5
    max_orders_per_min: int = 30
