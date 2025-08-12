# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : portfolio/state.py

Description :
Definit les modeles Pydantic representant l'etat courant du portefeuille.
Inclut la representation d'une position individuelle et un instantane global
du portefeuille (equity, cash, drawdown, exposition).

Utilise par :
    moteur de strategie (suivi des positions et equity)
    modules de risque et d'execution

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from pydantic import BaseModel


class Position(BaseModel):
    """Representation d'une position ouverte sur un instrument."""

    symbol: str
    qty: float
    avg_price: float
    side: str  # "long" ou "short"
    unrealized_pnl: float = 0.0


class PortfolioSnapshot(BaseModel):
    """Instantane global du portefeuille a un moment donne."""

    equity: float
    cash: float
    positions: list[Position] = []
    max_drawdown_pct: float = 0.0
    exposure_pct: float = 0.0
