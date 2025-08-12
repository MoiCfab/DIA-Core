"""Module src/dia_core/market_state/fake.py."""

from __future__ import annotations


def current_exposure_pct(equity: float, open_notional: float) -> float:
    """

    Args:
      equity: float:
      open_notional: float:

    Returns:

    """
    if equity <= 0:
        return 0.0
    return (open_notional / equity) * 100.0


def orders_last_min(_journal: object | None = None) -> int:
    """

    Args:
      _journal: object | None:  (Default value = None)

    Returns:

    """
    # Stub déterministe pour tests/CI
    return 0
