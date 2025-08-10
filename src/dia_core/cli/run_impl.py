# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

from contextlib import suppress
from typing import Any

from pandas import DataFrame


def get_last_window(symbol: str) -> DataFrame | None:  # pragma: no cover
    """Retourne une fenêtre OHLC si le provider est dispo, sinon None (safe)."""
    with suppress(Exception):
        from dia_core.data import provider as _prov  # runtime only

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
    """Exécute un cycle de décision (stub sûr pour V3). Retourne (ok, side)."""
    side: str | None = None
    px = 0.0
    with suppress(Exception):
        from dia_core.data import provider as _prov  # runtime only

        provider: Any = _prov
        px = float(provider.get_last_price(symbol))  # signature inconnue -> Any
    side = "buy" if px > 0.0 else None
    return True, side
