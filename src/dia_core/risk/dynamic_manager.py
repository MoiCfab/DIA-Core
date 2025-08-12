# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : risk/dynamic_manager.py

Description :
    Ajustements dynamiques des paramètres de risque en fonction du
    RegimeVector (stratégie métamorphe V3). Pur calcul, sans IO :
      - k_atr (volatilité)
      - risk_per_trade_pct
      - max_exposure_pct

Auteur : DYXIUM Invest / D.I.A. Core
"""
from __future__ import annotations

from dataclasses import dataclass

from dia_core.market_state.regime_vector import RegimeVector


@dataclass(frozen=True)
class DynamicRisk:
    """Ajuste SL/TP/sizing selon le régime et les limites."""

    k_atr: float
    risk_per_trade_pct: float
    max_exposure_pct: float


def adjust(reg: RegimeVector) -> DynamicRisk:
    """

    Args:
      reg: RegimeVector:

    Returns:

    """
    # Interpolations linéaires sur [0,1]
    k_atr = 1.2 + (3.5 - 1.2) * reg.score
    risk_per = 0.25 + (1.0 - 0.25) * reg.volatility  # plus de vol -> plus d'opportunités maîtrisées
    max_exp = 20.0 + (60.0 - 20.0) * reg.momentum  # marché porteur autorise + d'expo
    return DynamicRisk(
        k_atr=float(k_atr),
        risk_per_trade_pct=float(risk_per),
        max_exposure_pct=float(max_exp),
    )
