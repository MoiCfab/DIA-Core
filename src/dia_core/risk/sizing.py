from __future__ import annotations
from dataclasses import dataclass
from typing import Final

def _round_decimals(value: float, decimals: int) -> float:
    q: float = 10.0**decimals
    return int(value * q) / q

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

def compute_position_size_params(p: SizingParams) -> float:
    """Version groupée (V3) — préférée."""
    small: Final[float] = 1e-12
    if p.price <= 0 or p.atr <= 0 or p.equity <= 0:
        return 0.0
    risk_amount = p.equity * (p.risk_per_trade_pct / 100.0)
    stop_value = p.k_atr * p.atr
    if stop_value <= small:
        return 0.0
    qty_raw = (risk_amount / stop_value) / p.price
    qty = max(qty_raw, p.min_qty)
    notionnel = qty * p.price
    if notionnel < p.min_notional:
        qty = p.min_notional / p.price
    qty = _round_decimals(qty, p.qty_decimals)
    if qty < p.min_qty:
        qty = p.min_qty
    return max(qty, 0.0)

# Wrapper compat si tu as encore quelques appels anciens
def compute_position_size(
    *,
    equity: float,
    price: float,
    atr: float,
    risk_per_trade_pct: float,
    k_atr: float,
    min_qty: float,
    min_notional: float,
    qty_decimals: int,
) -> float:
    return compute_position_size_params(
        SizingParams(
            equity=equity,
            price=price,
            atr=atr,
            risk_per_trade_pct=risk_per_trade_pct,
            k_atr=k_atr,
            min_qty=min_qty,
            min_notional=min_notional,
            qty_decimals=qty_decimals,
        )
    )
