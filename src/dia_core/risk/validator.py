from __future__ import annotations
from dataclasses import dataclass
from dia_core.config.models import RiskLimits as ConfigRiskLimits
from pydantic import BaseModel

class ValidationResult(BaseModel):
    allowed: bool
    reason: str | None = None

@dataclass(frozen=True)
class OrderMetrics:
    current_exposure_pct: float
    projected_exposure_pct: float
    daily_loss_pct: float
    drawdown_pct: float
    orders_last_min: int

def validate_order_params(limits: ConfigRiskLimits, m: OrderMetrics) -> ValidationResult:
    if m.projected_exposure_pct > limits.max_exposure_pct:
        return ValidationResult(
            allowed=False,
            reason=(
                f"max_exposure_pct {m.projected_exposure_pct:.2f}% > "
                f"{limits.max_exposure_pct:.2f}%"
            ),
        )
    if m.daily_loss_pct > limits.max_daily_loss_pct:
        return ValidationResult(
            allowed=False,
            reason=(
                f"max_daily_loss_pct {m.daily_loss_pct:.2f}% > "
                f"{limits.max_daily_loss_pct:.2f}%"
            ),
        )
    if m.drawdown_pct > limits.max_drawdown_pct:
        return ValidationResult(
            allowed=False,
            reason=(
                f"max_drawdown_pct {m.drawdown_pct:.2f}% > "
                f"{limits.max_drawdown_pct:.2f}%"
            ),
        )
    if m.orders_last_min >= limits.max_orders_per_min:
        return ValidationResult(
            allowed=False,
            reason=(
                f"max_orders_per_min {m.orders_last_min} >= "
                f"{limits.max_orders_per_min}"
            ),
        )
    return ValidationResult(allowed=True)

# Wrapper compat si nécessaire
def validate_order(
    limits: ConfigRiskLimits,
    *,
    current_exposure_pct: float,
    projected_exposure_pct: float,
    daily_loss_pct: float,
    drawdown_pct: float,
    orders_last_min: int,
) -> ValidationResult:
    return validate_order_params(
        limits,
        OrderMetrics(
            current_exposure_pct=current_exposure_pct,
            projected_exposure_pct=projected_exposure_pct,
            daily_loss_pct=daily_loss_pct,
            drawdown_pct=drawdown_pct,
            orders_last_min=orders_last_min,
        ),
    )
