from __future__ import annotations

from typing import Final


def _round_decimals(value: float, decimals: int) -> float:
    q: float = 10.0**decimals
    return int(value * q) / q


def compute_position_size(
    *,
    equity: float,
    price: float,
    atr: float,  # mesure de volatilité (ex: ATR)
    risk_per_trade_pct: float,  # ex: 0.5 (%)
    k_atr: float,  # multiplicateur d'ATR pour le stop (ex: 2.0)
    min_qty: float,
    min_notional: float,
    qty_decimals: int,
) -> float:
    """
    Calcule une taille de position vol-aware:
    - Montant risqué = equity * (risk_per_trade_pct / 100)
    - Stop_value = k_atr * atr
    - qty_raw = (montant_risqué / stop_value) / price
    - Respect de min_qty, min_notional et décimales
    """
    SMALL: Final[float] = 1e-12
    if price <= 0 or atr <= 0 or equity <= 0:
        return 0.0

    risk_amount = equity * (risk_per_trade_pct / 100.0)
    stop_value = k_atr * atr
    if stop_value <= SMALL:
        return 0.0

    qty_raw = (risk_amount / stop_value) / price
    qty = max(qty_raw, min_qty)

    # Respect du min_notional
    notionnel = qty * price
    if notionnel < min_notional:
        qty = min_notional / price

    # Arrondi aux décimales permises par l'exchange
    qty = _round_decimals(qty, qty_decimals)
    if qty < min_qty:
        qty = min_qty

    return max(qty, 0.0)
