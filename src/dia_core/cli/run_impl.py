"""Module src/dia_core/cli/run_impl.py."""

# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

from contextlib import suppress
from typing import Any

from pandas import DataFrame
from dia_core.data import provider as _prov  # runtime only


def get_last_window(symbol: str) -> DataFrame | None:  # pragma: no cover
    """Retourne une fenêtre OHLC si le provider est dispo, sinon None (safe).

    Args:
      symbol: str:
      symbol: str:

    Returns:

    """
    with suppress(Exception):

        provider: Any = _prov
        win = provider.load_ohlc_window(symbol, 200)  # signature inconnue -> Any
        if isinstance(win, DataFrame):
            return win
    return None


def run_once(
    *,
    mode: str,
    symbol: str,
    k_atr_override: float | None = None,
) -> tuple[bool, str | None]:
    """Exécute un cycle de décision (stub sûr pour V3). Retourne (ok, side).

    Args:
      *:
      mode: str:
      symbol: str:
      k_atr_override: float | None:  (Default value = None)
      mode: str:
      symbol: str:
      k_atr_override: float | None:  (Default value = None)

    Returns:

    """
    side: str | None = None
    _mode = mode
    _k_atr_override = k_atr_override
    px = 0.0
    with suppress(Exception):

        provider: Any = _prov
        px = float(provider.get_last_price(symbol))  # signature inconnue -> Any
    side = "buy" if px > 0.0 else None
    return True, side
