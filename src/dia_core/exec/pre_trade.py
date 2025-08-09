from __future__ import annotations

from dataclasses import dataclass

from dia_core.config.models import AppConfig
from dia_core.config.models import RiskLimits as ConfigRiskLimits
from dia_core.kraken.types import OrderIntent
from dia_core.risk.errors import RiskLimitExceeded
from dia_core.risk.sizing import compute_position_size
from dia_core.risk.validator import ValidationResult, validate_order


# --- NEW: group params ---
@dataclass(frozen=True)
class MarketSnapshot:
    price: float
    atr: float
    k_atr: float = 2.0


@dataclass(frozen=True)
class RiskContext:
    equity: float
    current_exposure_pct: float
    orders_last_min: int


def pre_trade_checks(
    intent: OrderIntent,
    limits: ConfigRiskLimits,
    _equity: float,
    _min_notional: float,
) -> ValidationResult:
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


# --- REFACTORED: ≤ 5 params
def propose_order(
    *,
    cfg: AppConfig,
    market: MarketSnapshot,
    risk: RiskContext,
) -> dict[str, float]:
    qty = compute_position_size(
        equity=risk.equity,
        price=market.price,
        atr=market.atr,
        risk_per_trade_pct=cfg.risk.risk_per_trade_pct,
        k_atr=market.k_atr,
        min_qty=cfg.exchange.min_qty,
        min_notional=cfg.exchange.min_notional,
        qty_decimals=cfg.exchange.qty_decimals,
    )
    notional = qty * market.price
    projected_exposure_pct = risk.current_exposure_pct + (notional / risk.equity) * 100.0

    res = validate_order(
        cfg.risk,
        current_exposure_pct=risk.current_exposure_pct,
        projected_exposure_pct=projected_exposure_pct,
        daily_loss_pct=0.0,  # TODO: brancher métrique réelle
        drawdown_pct=0.0,  # TODO: idem
        orders_last_min=risk.orders_last_min,
    )
    if not res.allowed:
        raise RiskLimitExceeded(res.reason or "Risk limit violated")
    return {"qty": qty, "notional": notional}


# --- Optional: wrapper pour compat si ailleurs non modifié
def propose_order_legacy(
    *,
    cfg: AppConfig,
    equity: float,
    price: float,
    atr: float,
    current_exposure_pct: float,
    orders_last_min: int,
    k_atr: float = 2.0,
) -> dict[str, float]:
    market = MarketSnapshot(price=price, atr=atr, k_atr=k_atr)
    risk = RiskContext(
        equity=equity, current_exposure_pct=current_exposure_pct, orders_last_min=orders_last_min
    )
    return propose_order(cfg=cfg, market=market, risk=risk)
