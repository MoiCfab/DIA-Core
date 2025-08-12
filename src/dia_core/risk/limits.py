# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : risk/limits.py

Description :
Definit le modèle Pydantic représentant l'ensemble des limites de risque
utilisées par DIA-Core pour encadrer l'activité de trading.
Ces limites sont appliquées par le validateur de risque avant chaque execution.

Utilise par :
    config/models.py (configuration par défaut)
    exec/pre_trade.py et risk/validator.py (verifications runtime)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from pydantic import BaseModel


class RiskLimits(BaseModel):
    """Limites de risque appliquées au portefeuille et aux ordres.

    Attributes :
        max_daily_loss_pct : Perte journalière maximale autorisée (en % d'equite).
        max_drawdown_pct : Drawdown maximal toléré (en %).
        max_exposure_pct : Exposition maximale sur le marché (en % d'equite).
        risk_per_trade_pct : Risque maximum alloué par trade (en % d'equite).
        max_orders_per_min : Nombre maximum d'ordres autorisés par minute.

    Args:

    Returns:

    """

    max_daily_loss_pct: float = 2.0
    max_drawdown_pct: float = 15.0
    max_exposure_pct: float = 50.0
    risk_per_trade_pct: float = 0.5
    max_orders_per_min: int = 30
