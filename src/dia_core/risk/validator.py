from __future__ import annotations

from dataclasses import dataclass

from dia_core.config.models import RiskLimits as ConfigRiskLimits
from dia_core.risk.errors import RiskLimitExceededError
from pydantic import BaseModel


class ValidationResult(BaseModel):
    allowed: bool
    reason: str | None = None


@dataclass(frozen=True)
class RiskCheckParams:
    current_exposure_pct: float
    projected_exposure_pct: float
    daily_loss_pct: float
    drawdown_pct: float
    orders_last_min: int


def validate_order(limits: ConfigRiskLimits, params: RiskCheckParams) -> None:
    if params.projected_exposure_pct > limits.max_exposure_pct:
        raise RiskLimitExceededError(
            f"max_exposure_pct {params.projected_exposure_pct:.2f}% > {limits.max_exposure_pct:.2f}%"
        )
    if params.daily_loss_pct > limits.max_daily_loss_pct:
        raise RiskLimitExceededError(
            f"max_daily_loss_pct {params.daily_loss_pct:.2f}% > {limits.max_daily_loss_pct:.2f}%"
        )
    if params.drawdown_pct > limits.max_drawdown_pct:
        raise RiskLimitExceededError(
            f"max_drawdown_pct {params.drawdown_pct:.2f}% > {limits.max_drawdown_pct:.2f}%"
        )
    if params.orders_last_min > limits.max_orders_per_min:
        raise RiskLimitExceededError(
            f"max_orders_per_min {params.orders_last_min} > {limits.max_orders_per_min}"
        )