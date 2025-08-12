"""Modèles backtest: conteneurs de paramètres simples, sans logique I/O."""

from dataclasses import dataclass
from typing import Literal

Side = Literal["buy", "sell"]


@dataclass(frozen=True)
class CloseOpenParams:
    """Paramètres pour clôture/ouverture de position en backtest."""

    equity: float
    position: float
    prev_price: float
    current_price: float
    fee_bps: float
    intent_side: Side | None
