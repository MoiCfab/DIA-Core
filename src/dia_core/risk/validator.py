# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : risk/validator.py

Description :
Fournit les structures de donnees et la fonction centrale pour valider
qu'un ordre respecte toutes les limites de risque configurées dans DIA-Core.
Si une limite est dépassée, une exception RiskLimitExceededError est levee.

Utilise par :
    exec/pre_trade.py (contrôle de risque avant execution)
    exec/executor.py (rejet des ordres non conformes)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from dia_core.config.models import RiskLimits as ConfigRiskLimits
from dia_core.risk.errors import RiskLimitExceededError


class ValidationResult(BaseModel):
    """Résultat d'une validation de risque.

    Attributes :
        allowed : True si l'ordre est autorisé, False sinon.
        reason : Raison du rejet si applicable.
    """

    allowed: bool
    reason: str | None = None


@dataclass(frozen=True)
class RiskCheckParams:
    """Paramètres observes pour verifier le respect des limites de risque.

    Attributes :
        current_exposure_pct : Exposition actuelle du portefeuille (en %).
        projected_exposure_pct : Exposition projetée apres l'ordre (en %).
        daily_loss_pct : Perte réalisée du jour (en % de l'equite).
        drawdown_pct : Drawdown courant (en % de l'equite).
        orders_last_min : Nombre d'ordres passes sur la dernière minute.
    """

    current_exposure_pct: float
    projected_exposure_pct: float
    daily_loss_pct: float
    drawdown_pct: float
    orders_last_min: int


def validate_order(limits: ConfigRiskLimits, params: RiskCheckParams) -> None:
    """Vérifié qu'un ordre respecte toutes les limites de risque.

    Args :
        limits : Configuration des limites de risque.
        params : Mesures actuelles et projetées du portefeuille.

    Raises :
        RiskLimitExceededError : Si une limite est dépassée.
    """
    if params.projected_exposure_pct > limits.max_exposure_pct:
        raise RiskLimitExceededError(
            f"max_exposure_pct {params.projected_exposure_pct:.2f}% "
            f"> {limits.max_exposure_pct:.2f}%"
        )
    if params.daily_loss_pct > limits.max_daily_loss_pct:
        raise RiskLimitExceededError(
            f"max_daily_loss_pct {params.daily_loss_pct:.2f}% > {limits.max_daily_loss_pct:.2f}%"
        )
    if params.drawdown_pct > limits.max_drawdown_pct:
        raise RiskLimitExceededError(
            f"max_drawdown_pct {params.drawdown_pct:.2f}% > {limits.max_drawdown_pct:.2f}%"
        )
    if params.orders_last_min > limits.max_orders_per_min:
        raise RiskLimitExceededError(
            f"max_orders_per_min {params.orders_last_min} > {limits.max_orders_per_min}"
        )
