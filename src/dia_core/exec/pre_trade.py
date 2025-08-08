from __future__ import annotations

from typing import Dict, Any

from dia_core.kraken.types import OrderIntent
from dia_core.config.models import AppConfig
from dia_core.risk.sizing import compute_position_size
from dia_core.risk.validator import validate_order, ValidationResult
from dia_core.risk.errors import RiskLimitExceeded
from dia_core.risk.limits import RiskLimits


def pre_trade_checks(
    intent: OrderIntent, limits: RiskLimits, equity: float, min_notional: float
) -> ValidationResult:
    """Applique les validations avant l'envoi d'un ordre."""
    # Ici on suppose que 'limits' est déjà un objet RiskLimits
    # et que les autres paramètres nécessaires sont accessibles via 'intent'
    # À adapter si tes données viennent d'ailleurs.

    current_exposure_pct: float = getattr(intent, "current_exposure_pct", 0.0)
    projected_exposure_pct: float = getattr(intent, "projected_exposure_pct", 0.0)
    daily_loss_pct: float = getattr(intent, "daily_loss_pct", 0.0)
    drawdown_pct: float = getattr(intent, "drawdown_pct", 0.0)
    orders_last_min: int = getattr(intent, "orders_last_min", 0)


    return validate_order(
        limits,
        current_exposure_pct=current_exposure_pct,
        projected_exposure_pct = projected_exposure_pct,
        daily_loss_pct = daily_loss_pct,
        drawdown_pct = drawdown_pct,
        orders_last_min = orders_last_min,
    )


def propose_order(
    *,
    cfg: AppConfig,
    equity: float,
    price: float,
    atr: float,
    current_exposure_pct: float,
    orders_last_min: int,
    k_atr: float = 2.0,
) -> Dict[str, float]:
    """
    Calcule une quantité et valide les limites. Raise si violation (hard-stop).
    Retour: {"qty": ..., "notional": ...}
    """
    qty = compute_position_size(
        equity=equity,
        price=price,
        atr=atr,
        risk_per_trade_pct=cfg.risk.risk_per_trade_pct,
        k_atr=k_atr,
        min_qty=cfg.exchange.min_qty,
        min_notional=cfg.exchange.min_notional,
        qty_decimals=cfg.exchange.qty_decimals,
    )
    notional = qty * price
    projected_exposure_pct = current_exposure_pct + (notional / equity) * 100.0

    res = validate_order(
        cfg.risk,
        current_exposure_pct=current_exposure_pct,
        projected_exposure_pct=projected_exposure_pct,
        daily_loss_pct=0.0,  # à injecter depuis le monitoring PnL
        drawdown_pct=0.0,  # idem
        orders_last_min=orders_last_min,
    )
    if not res.allowed:
        raise RiskLimitExceeded(res.reason or "Risk limit violated")

    return {"qty": qty, "notional": notional}
