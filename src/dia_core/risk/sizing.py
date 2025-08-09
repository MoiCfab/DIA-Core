from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class SizingParams:
    equity: float
    price: float
    atr: float
    risk_per_trade_pct: float
    k_atr: float
    min_qty: float
    min_notional: float
    qty_decimals: int


def compute_position_size(params: SizingParams) -> float:
    """Calcule la taille de position en fonction des paramètres de sizing."""
    small: Final[float] = 1e-12
    if params.price <= 0 or params.atr <= 0 or params.equity <= 0:
        return 0.0

    risk_amount = params.equity * (params.risk_per_trade_pct / 100.0)
    raw_qty = risk_amount / (params.k_atr * params.atr)
    qty = round(max(raw_qty, params.min_qty), params.qty_decimals)

    if qty * params.price < params.min_notional:
        return 0.0

    return max(qty, small)
