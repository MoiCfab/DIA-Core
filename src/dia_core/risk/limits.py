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

from dia_core.config.models import RiskLimits

__all__ = ["RiskLimits"]
