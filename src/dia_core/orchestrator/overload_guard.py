# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : overload_guard.py

Description :
Garde-fou pour la gestion des surcharges systeme dans DIA-Core.
Ne degrade jamais le modele IA. En cas de surcharge persistante,
desactive des paires non prioritaires et alerte par email.

Utilise par :
    orchestrateur ou boucle principale pour ajuster la charge runtime.

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from collections.abc import Sequence
import contextlib
import logging

from dia_core.alerts.email_alerts import EmailAlerter
from dia_core.monitor.health_monitor import HealthMonitor, Thresholds

logger = logging.getLogger(__name__)


class OverloadGuard:
    """Surveillance et reduction de charge sans downgrade du modele IA.

    Comportement :
      - En cas de surcharge soutenue, retire un nombre limite de paires
        issues de la liste des paires non prioritaires.
      - Envoie une alerte email detaillee pour signaler l'action.
      - L'appelant decide ensuite si cette reduction est conservee ou si
        le materiel est augmenté.
    """

    def __init__(self, alerter: EmailAlerter, thresholds: Thresholds | None = None) -> None:
        """Initialise le garde-fou avec un alerter et des seuils.

        Args:
            alerter: Instance de EmailAlerter pour envoyer les alertes.
            thresholds: Seuils CPU/RAM/latence a surveiller.
        """
        self.hm = HealthMonitor(thresholds or Thresholds())
        self.alerter = alerter

    def tick(
        self,
        active_pairs: Sequence[str],
        low_priority_pairs: Sequence[str],
        avg_cycle_latency_ms: float,
    ) -> list[str]:
        """Effectue un cycle de surveillance et ajuste la liste des paires.

        Echantillonne la charge systeme, evalue si surcharge persistante,
        et si besoin retire des paires non prioritaires.
        Envoie un email pour signaler l'action.

        Args:
            active_pairs: Liste des paires actuellement actives.
            low_priority_pairs: Liste des paires consideres comme moins critiques.
            avg_cycle_latency_ms: Latence moyenne d'un cycle de stratégie.

        Returns:
            Nouvelle liste de paires actives apres éventuelle reduction.
        """
        self.hm.sample(latency_ms=avg_cycle_latency_ms)
        decision = self.hm.evaluate(active_pairs, low_priority_pairs)

        if not decision.overloaded:
            return list(active_pairs)

        # Selection des paires à retirer (debut de la liste low_priority)
        to_disable = list(low_priority_pairs)[: decision.drop_pairs]
        new_list = [p for p in active_pairs if p not in to_disable]

        # Construction du message d'alerte
        subject = "[DIA-Core] Surcharge détectée - reduction du périmètre"
        body = (
            "Surcharge soutenue détectée (" + (decision.reason or "") + ")\n"
            f"Paires actives: {len(active_pairs)} -> {len(new_list)} (-{decision.drop_pairs})\n"
            f"Paires désactivées: {to_disable}\n"
            "Action requise: verifier optimisation ou augmenter la capacité.\n"
        )

        # Tentative d'envoi de l'alerte
        with contextlib.suppress(Exception):
            try:
                self.alerter.send(subject, body)
            except Exception as err:
                logger.warning("Alerte email échouée: %s", err)
                raise

        return new_list
