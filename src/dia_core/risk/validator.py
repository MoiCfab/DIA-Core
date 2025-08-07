from __future__ import annotations
from pydantic import BaseModel
from dia_core.kraken.types import OrderIntent
from dia_core.risk.limits import RiskLimits

class ValidationResult(BaseModel):
    ok: bool
    reason: str = ""

def validate_order(intent: OrderIntent, limits: RiskLimits, equity: float, exchange_min_notional: float) -> ValidationResult:
    """Valide un ordre selon les règles de risque et contraintes exchange."""
    notional = (intent.limit_price or 0.0) * intent.qty if intent.type == "limit" else 0.0
    if notional and notional < exchange_min_notional:
        return ValidationResult(ok=False, reason=f"MIN_NOTIONAL {notional} < {exchange_min_notional}")

    max_risk = equity * (limits.risk_per_trade_pct / 100.0)
    if intent.type == "limit" and notional > 0 and notional > max_risk * 20:
        return ValidationResult(ok=False, reason=f"NOTIONAL_TOO_LARGE {notional:.2f} > cap")

    return ValidationResult(ok=True)
