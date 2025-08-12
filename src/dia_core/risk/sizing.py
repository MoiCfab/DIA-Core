# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : risk/sizing.py

Description :
Calcule la taille optimale d'une position en fonction des paramètres
de risque, du capital disponible et de la volatilité (ATR).
Assure le respect des contraintes minimales (quantité minimale, notionnel minimal).

Utilise par :
    exec/pre_trade.py (proposition d'ordre)
    moteurs de stratégie utilisant la gestion de position dynamique

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class SizingParams:
    """Paramètres necessaires pour calculer la taille d'une position.

    Attributes :
        equity : Capital total disponible.
        price : Prix actuel de l'actif.
        atr : Average True Range (volatilité) de l'actif.
        risk_per_trade_pct : Pourcentage du capital à risquer par trade.
        k_atr : Multiplicateur ATR pour définir la taille du stop.
        min_qty : Quantité minimale autorisée par l'exchange.
        min_notional : Valeur notionnelle minimale (prix * quantité).
        qty_decimals : Nombre de décimales autorisées pour la quantité.

    Args:

    Returns:

    """

    equity: float
    price: float
    atr: float
    risk_per_trade_pct: float
    k_atr: float
    min_qty: float
    min_notional: float
    qty_decimals: int


def compute_position_size(params: SizingParams) -> float:
    """Calcule la taille de position en fonction des paramètres de sizing.

    La taille est déterminée par le montant à risque, la volatilité (ATR)
    et le multiplicateur ATR. Les contraintes de quantité minimale et de
    valeur notionnelle minimale sont appliquées.

    Args :

    Args:
      params: SizingParams:

    Returns:
      Taille de position (quantité) arrondie aux décimales autorisées.
      Retourne 0.0 si les conditions minimales ne sont pas remplies.

    """
    small: Final[float] = 1e-12
    if params.price <= 0 or params.atr <= 0 or params.equity <= 0:
        return 0.0

    risk_amount = params.equity * (params.risk_per_trade_pct / 100.0)
    raw_qty = risk_amount / (params.k_atr * params.atr)
    qty = round(max(raw_qty, params.min_qty), params.qty_decimals)

    if qty * params.price < params.min_notional:
        return 0.0

    return max(qty, small)
