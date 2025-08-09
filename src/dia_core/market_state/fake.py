from __future__ import annotations


def current_exposure_pct(equity: float, open_notional: float) -> float:
    if equity <= 0:
        return 0.0
    return (open_notional / equity) * 100.0

def orders_last_min(_journal: object | None = None) -> int:
    # Stub déterministe pour tests/CI
    return 0
