from __future__ import annotations

from dia_core.kraken.types import OrderIntent
from dia_core.config.models import AppConfig, RiskLimits as ConfigRiskLimits
from dia_core.risk.sizing import compute_position_size
from dia_core.risk.validator import validate_order, ValidationResult
from dia_core.risk.errors import RiskLimitExceeded


def pre_trade_checks(
    intent: OrderIntent,
    limits: ConfigRiskLimits,
    _equity: float,
    _min_notional: float,
) -> ValidationResult:
    """
    Applique les validations "hard-stop" avant envoi d'un ordre.
    Les valeurs nécessaires sont lues sur `intent` (si absentes, défauts à 0).
    """
    current_exposure_pct: float = getattr(intent, "current_exposure_pct", 0.0)
    projected_exposure_pct: float = getattr(intent, "projected_exposure_pct", 0.0)
    daily_loss_pct: float = getattr(intent, "daily_loss_pct", 0.0)
    drawdown_pct: float = getattr(intent, "drawdown_pct", 0.0)
    orders_last_min: int = getattr(intent, "orders_last_min", 0)

    return validate_order(
        limits,
        current_exposure_pct=current_exposure_pct,
        projected_exposure_pct=projected_exposure_pct,
        daily_loss_pct=daily_loss_pct,
        drawdown_pct=drawdown_pct,
        orders_last_min=orders_last_min,
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
) -> dict[str, float]:
    """
    Calcule une quantité vol-aware et valide les limites. Lève RiskLimitExceeded si violation.
    Retour: {"qty": <float>, "notional": <float>}
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

    # Projection d'exposition après ce trade
    projected_exposure_pct = current_exposure_pct + (notional / equity) * 100.0

    res = validate_order(
        cfg.risk,
        current_exposure_pct=current_exposure_pct,
        projected_exposure_pct=projected_exposure_pct,
        daily_loss_pct=0.0,  # TODO: brancher métrique réelle depuis le monitoring PnL
        drawdown_pct=0.0,    # TODO: idem
        orders_last_min=orders_last_min,
    )
    if not res.allowed:
        raise RiskLimitExceeded(res.reason or "Risk limit violated")

    return {"qty": qty, "notional": notional}
