# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : exec/executor.py

Description :
Exécuteur d`ordres centralisé pour DIA-Core. Ce composant orchestre :
    la validation pré-trade (limites de risque, notionnel minimal, etc.) ;
    les différents modes d`exécution : "dry_run", "paper", "live" ;
    la construction du payload et l`envoi sécurisé vers l`exchange (validate=true).

Il garantit qu`aucun ordre ne part en production sans passer par les contrôles
de risque et, en mode "live", sans confirmation interactive si exigée.

Utilisé par :
    cli/main.py (soumission d`exemple et démonstration)
    stratégies/runtime (soumission réelle après décision)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import logging
from typing import Literal
import uuid

from dia_core.config.models import RiskLimits as ConfigRiskLimits
from dia_core.exec.pre_trade import pre_trade_checks
from dia_core.kraken.client import KrakenClient
from dia_core.kraken.types import OrderIntent, SubmittedOrder
from dia_core.risk.errors import RiskLimitExceededError

logger = logging.getLogger(__name__)
Mode = Literal["dry_run", "paper", "live"]


class Executor:
    """Gestionnaire d`exécution des ordres.

    Rôle :
        Appliquer les contrôles de risque avant tout envoi (pré-trade).
        Simuler ("dry_run") ou journaliser sans envoi ("paper") pour tests.
        En mode "live", exiger une confirmation utilisateur et utiliser la
          validation serveur ("validate=true") chez Kraken avant exécution.

    Attributs :
        client : Client d`accès à l`API exchange.
        mode : Mode d`exécution courant.
        min_notional : Notionnel minimal accepté (sécurité locale).
        limits : Limites de risque actives (issues de la config).
        require_interactive_confirm : Demande de confirmation en mode "live".
    """

    def __init__(
        self,
        client: KrakenClient,
        mode: Mode = "dry_run",
        min_notional: float = 10.0,
        limits: ConfigRiskLimits | None = None,
        require_interactive_confirm: bool = True,
    ):
        """Crée un exécuteur.

        Args :
            client : Client Kraken initialisé.
            mode : Mode d`exécution ("dry_run", "paper", "live").
            min_notional : Notionnel minimum toléré localement.
            limits : Limites de risque ; par défaut, une instance neutre.
            require_interactive_confirm : Si vrai, confirmation manuelle requise en "live".
        """
        self.client = client
        self.mode = mode
        self.min_notional = min_notional
        # Utilise le modèle de config (attendu par pre_trade_checks / validate_order)
        self.limits: ConfigRiskLimits = limits or ConfigRiskLimits()
        self.require_interactive_confirm = require_interactive_confirm

    def _confirm_live(self) -> None:
        """Demande une confirmation interactive en mode "live".

        Raises :
            SystemExit : Si l`utilisateur n`entre pas exactement "YES".
        """
        if self.mode == "live" and self.require_interactive_confirm:
            answer = input("LIVE MODE: tapez 'YES' pour confirmer : ").strip()
            if answer != "YES":
                raise SystemExit("Live submission annulée par l'utilisateur.")

    def submit(self, intent: OrderIntent, equity: float) -> SubmittedOrder:
        """Soumet un ordre après contrôles de risque.

        Pipeline :
            1) Contrôles pré-trade (exposition, pertes max, cadence, notionnel, etc.).
            2) Selon "mode" :
               - "dry_run" : ordre simulé et accepté localement.
               - "paper" : ordre enregistré (pas d`envoi exchange).
               - "live" : confirmation interactive puis `validate=true` chez Kraken.

        Args :
            intent : Intention d`ordre (symbole, côté, type, quantité, prix limite).
            equity : Équité courante du compte (pour sizing/contrôles).

        Returns :
            Résultat local de soumission (id client, statut, raison éventuelle).

        Notes:
            - En "live", on utilise "validate=true" ("dry-run" côté Kraken) pour
              sécuriser le payload avant envoi réel (étape distincte possible).
        """
        # Validation risque (hard-stop)
        try:
            pre_trade_checks(intent, self.limits, equity, self.min_notional)
        except RiskLimitExceededError as e:
            logger.warning(
                "Ordre refusé",
                extra={"extra": {"component": "executor", "reason": str(e)}},
            )
            return SubmittedOrder(
                client_order_id=str(uuid.uuid4()),
                status="rejected",
                reason=str(e),
            )

        if self.mode == "dry_run":
            logger.info(
                "Dry-run : ordre simulé",
                extra={"extra": {"component": "executor"}},
            )
            return SubmittedOrder(client_order_id=str(uuid.uuid4()), status="accepted")

        if self.mode == "paper":
            logger.info(
                "Paper : ordre enregistré (pas d'envoi exchange)",
                extra={"extra": {"component": "executor"}},
            )
            return SubmittedOrder(client_order_id=str(uuid.uuid4()), status="accepted")

        # LIVE MODE
        self._confirm_live()
        payload = {
            "pair": intent.symbol,
            "type": intent.side,
            "ordertype": intent.type,
            "volume": f"{intent.qty}",
            "validate": "true",  # Kraken dry-run interne pour sécuriser
        }
        if intent.type == "limit" and intent.limit_price:
            payload["price"] = f"{intent.limit_price}"

        self.client.add_order(payload)
        logger.info(
            "Ordre validé par Kraken (validate=true)",
            extra={"extra": {"component": "executor"}},
        )
        return SubmittedOrder(client_order_id=str(uuid.uuid4()), status="accepted")
