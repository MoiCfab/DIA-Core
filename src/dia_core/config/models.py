# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : config/models.py

Description :
Définit les modèles de configuration pour DIA-Core à l'aide de Pydantic.
Ces modèles centralisent et valident tous les paramètres du bot, tels que :
    les informations liées à l'exchange,
    les limites de risque,
    les chemins de stockage et paramètres globaux.

Utilisé par :
    onfig/loader.py (chargement et validation de la configuration)
    main.py (initialisation des composants principaux)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Mode = Literal["dry_run", "paper", "live"]


class ExchangeMeta(BaseModel):
    """Métadonnées de l'exchange et contraintes associées.

    Attributes :
        symbol : Paire de trading (ex : 'BTC/EUR').
        price_decimals : Nombre de décimales pour le prix.
        qty_decimals : Nombre de décimales pour la quantité.
        min_qty : Quantité minimale autorisée.
        min_notional : Notionnel minimal (prix * quantité) autorisé.

    Args:

    Returns:

    """

    symbol: str = Field(..., description="Paire ex: 'BTC/EUR'")
    price_decimals: int = 2
    qty_decimals: int = 6
    min_qty: float = 0.0001
    min_notional: float = 10.0


class RiskLimits(BaseModel):
    """Paramètres de gestion du risque."""

    max_daily_loss_pct: float = 2.0
    max_drawdown_pct: float = 15.0
    max_exposure_pct: float = 50.0
    risk_per_trade_pct: float = 0.5
    max_orders_per_min: int = 30


class AppConfig(BaseModel):
    """Configuration principale de DIA-Core.

    Attributes :
        mode : Mode d'exécution ("dry_run", "paper", "live").
        exchange : Métadonnées et contraintes liées à l'exchange.
        risk : Paramètres de gestion du risque.
        data_window_bars : Nombre de bougies conservées en mémoire pour les indicateurs.
        cache_dir : Répertoire pour le cache local.
        journal_path : Chemin vers la base SQLite du journal.
        log_dir : Répertoire des logs.
        pair : Paire de trading principale.
        require_interactive_confirm : Demande une confirmation manuelle avant exécution réelle.

    Args:

    Returns:

    """

    mode: Mode = "dry_run"
    exchange: ExchangeMeta
    risk: RiskLimits = RiskLimits()
    data_window_bars: int = 1000
    cache_dir: str = "state/cache"
    journal_path: str = "state/journal.sqlite"
    log_dir: str = "logs"
    pair: str = "XXBTZEUR"
    require_interactive_confirm: bool = True

    @field_validator("mode")
    @classmethod
    def warn_if_live(cls, v: Mode) -> Mode:
        """Affiche un avertissement si le mode "live" est activé.

        Args :
            v: Valeur du champ "mode".

        Returns :
            La valeur inchangée de "mode".

        Notes :
            Cette validation n'empêche pas l'exécution en mode "live", mais
            signale à l'utilisateur que le bot sera en conditions réelles.

        Args:
          v: Mode:

        Returns:

        """
        if v == "live":
            print("[SECURITY] Attention: mode LIVE activé")
        return v
