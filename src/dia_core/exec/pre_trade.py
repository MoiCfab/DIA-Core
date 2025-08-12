# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : exec/pre_trade.py

Description :
Effectue les contrôles de risque pré-trade pour DIA-Core avant toute soumission d`ordre.
Ces contrôles incluent :
- l`exposition courante et projetée,
- les pertes journalières,
- le drawdown,
- la limite du nombre d`ordres par minute.

Utilisé par :
    exec/executor.py (contrôle bloquant avant envoi d`ordre)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from dataclasses import dataclass

from dia_core.config.models import AppConfig, RiskLimits as ConfigRiskLimits
from dia_core.kraken.types import OrderIntent
from dia_core.risk.sizing import SizingParams, compute_position_size
from dia_core.risk.validator import RiskCheckParams, validate_order


# --- NEW: group params ---
@dataclass(frozen=True)
class MarketSnapshot:
    """Instante de marche pour le sizing.

    Attributes :
        price : Dernier prix observe.
        atr : Average True Range en unite de prix.
        k_atr : Multiplicateur d'ATR pour calibrer le stop cible.
    """

    price: float
    atr: float
    k_atr: float = 2.0


@dataclass(frozen=True)
class RiskContext:
    """Contexte de risque courant.

    Attributes :
        equity : Equite totale disponible (devise du compte).
        current_exposure_pct : Exposition actuelle totale en pourcentage d'equite.
        orders_last_min : Nombre d'ordres émis sur la dernière minute.
    """

    equity: float
    current_exposure_pct: float
    orders_last_min: int


def pre_trade_checks(
    intent: OrderIntent,
    limits: ConfigRiskLimits,
    _equity: float,
    _min_notional: float,
) -> None:
    """Effectue les verifications de risque avant d'envoyer un ordre.

    Les valeurs necessaires sont extraites dynamiquement de `intent` si presentes,
    sinon remplacees par des valeurs par defaut (0.0 ou 0). La fonction est
    volontairement side-effect free et ne modifie pas `intent`.

    Args :
        intent : Intention d'ordre contenant symbole, type, quantite et, si
            disponibles, metriques de risque (exposition, drawdown, etc.).
        limits : Limites de risque configurees (exposition max, pertes journaliere,
            drawdown max, cadence d'ordres).
        equity : Equite courante du compte. Parametre disponible pour des
            controles elargis si necessaire.
        min_notional : Notionnel minimal local. Parametre reserve pour des
            controles complementaires.

    Raises:
        RiskLimitExceededError: Si une contrainte de `limits` est depassee.
    """
    current_exposure_pct: float = getattr(intent, "current_exposure_pct", 0.0)
    projected_exposure_pct: float = getattr(intent, "projected_exposure_pct", 0.0)
    daily_loss_pct: float = getattr(intent, "daily_loss_pct", 0.0)
    drawdown_pct: float = getattr(intent, "drawdown_pct", 0.0)
    orders_last_min: int = getattr(intent, "orders_last_min", 0)

    metrics = RiskCheckParams(
        current_exposure_pct=current_exposure_pct,
        projected_exposure_pct=projected_exposure_pct,
        daily_loss_pct=daily_loss_pct,
        drawdown_pct=drawdown_pct,
        orders_last_min=orders_last_min,
    )
    validate_order(limits, metrics)


def propose_order(*, cfg: AppConfig, market: MarketSnapshot, risk: RiskContext) -> dict[str, float]:
    """Propose une quantite et un notionnel conformes aux limites de risque.

    La quantite est derivee d'un schema de budget de risque base sur l'ATR et
    les contraintes d'exchange provenant de `cfg.exchange`. Une fois la quantite
    estimee, la fonction calcule l'exposition projetee et valide les limites.

    Args :
        cfg : Configuration complete du bot incluant `exchange` et `risk`.
        market : Instante de marche courant (prix, ATR, facteur k_atr).
        risk : Contexte de risque (equite, exposition actuelle, cadence).

    Returns :
        Un dictionnaire :
            - "qty" : quantité proposee (apres arrondis et minimas).
            - "notional" : notionnel correspondant (qty * prix).

    Raises :
        RiskLimitExceededError : Si l'ordre projetterait une exposition au-dela
            des limites de `cfg.risk`.
    """
    params = SizingParams(
        equity=risk.equity,
        price=market.price,
        atr=market.atr,
        risk_per_trade_pct=cfg.risk.risk_per_trade_pct,
        k_atr=market.k_atr,
        min_qty=cfg.exchange.min_qty,
        min_notional=cfg.exchange.min_notional,
        qty_decimals=cfg.exchange.qty_decimals,
    )
    qty = compute_position_size(params)
    notional = qty * market.price
    projected_exposure_pct = risk.current_exposure_pct + (notional / risk.equity) * 100.0

    metrics = RiskCheckParams(
        current_exposure_pct=risk.current_exposure_pct,
        projected_exposure_pct=projected_exposure_pct,
        daily_loss_pct=0.0,
        drawdown_pct=0.0,
        orders_last_min=risk.orders_last_min,
    )
    validate_order(cfg.risk, metrics)  # lève si violation
    return {"qty": qty, "notional": notional}
