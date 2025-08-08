from __future__ import annotations

from pydantic import BaseModel
from typing import Optional

from dia_core.config.models import RiskLimits


class ValidationResult(BaseModel):
    allowed: bool
    reason: Optional[str] = None


def validate_order(
    limits: RiskLimits,
    *,
    current_exposure_pct: float,
    projected_exposure_pct: float,
    daily_loss_pct: float,
    drawdown_pct: float,
    orders_last_min: int,
) -> ValidationResult:
    """
    Vérifie les limites 'hard-stop'. La première violation bloque.
    """
    if projected_exposure_pct > limits.max_exposure_pct:
        return ValidationResult(
            allowed=False,
            reason=f"max_exposure_pct {projected_exposure_pct:.2f}% > {limits.max_exposure_pct:.2f}%",
        )

    if daily_loss_pct > limits.max_daily_loss_pct:
        return ValidationResult(
            allowed=False,
            reason=f"max_daily_loss_pct {daily_loss_pct:.2f}% > {limits.max_daily_loss_pct:.2f}%",
        )

    if drawdown_pct > limits.max_drawdown_pct:
        return ValidationResult(
            allowed=False,
            reason=f"max_drawdown_pct {drawdown_pct:.2f}% > {limits.max_drawdown_pct:.2f}%",
        )

    if orders_last_min >= limits.max_orders_per_min:
        return ValidationResult(
            allowed=False,
            reason=f"max_orders_per_min {orders_last_min} >= {limits.max_orders_per_min}",
        )

    # Exposition actuelle informatif; le blocage se fait sur la projection
    return ValidationResult(allowed=True)
