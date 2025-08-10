# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : risk/errors.py

Description :
Definit l'exception levee lorsque qu'un trade viole une ou plusieurs
limites de risque définies dans la configuration DIA-Core.

Utilise par :
    exec/pre_trade.py (verifications de risque avant execution)
    risk/validator.py (contrôle central des contraintes)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations


class RiskLimitExceededError(RuntimeError):
    """Exception levee lorsqu'un ordre dépasse au moins une limite de risque (hard-stop)."""
