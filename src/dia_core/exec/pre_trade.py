from __future__ import annotations
from dia_core.kraken.types import OrderIntent
from dia_core.risk.validator import validate_order, RiskLimits, ValidationResult


def pre_trade_checks(
    intent: OrderIntent, limits: RiskLimits, equity: float, min_notional: float
) -> ValidationResult:
    """Applique les validations avant l'envoi d'un ordre."""
    return validate_order(intent, limits, equity, min_notional)
