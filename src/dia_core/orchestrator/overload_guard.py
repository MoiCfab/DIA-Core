from __future__ import annotations
from typing import Sequence
from dia_core.monitor.health_monitor import HealthMonitor, Thresholds
from dia_core.alerts.email_alerts import EmailAlerter


class OverloadGuard:
    """Garde-fou: ne JAMAIS downgrader le modèle.

    - En surcharge soutenue: on retire des paires non prioritaires et on ALERTE par email.
    - L'appelant décide ensuite de persister cette réduction (config) ou d'augmenter le hardware.
    """

    def __init__(self, alerter: EmailAlerter, thresholds: Thresholds | None = None) -> None:
        self.hm = HealthMonitor(thresholds or Thresholds())
        self.alerter = alerter

    def tick(
        self,
        active_pairs: Sequence[str],
        low_priority_pairs: Sequence[str],
        avg_cycle_latency_ms: float,
    ) -> list[str]:
        """Retourne la nouvelle liste de paires actives après décision (éventuellement réduite)."""
        self.hm.sample(latency_ms=avg_cycle_latency_ms)
        decision = self.hm.evaluate(active_pairs, low_priority_pairs)
        if not decision.overloaded:
            return list(active_pairs)
        # Construire nouvelle liste en retirant les 'drop_pairs' depuis la fin de la low_priority list
        to_disable = list(low_priority_pairs)[: decision.drop_pairs]
        new_list = [p for p in active_pairs if p not in to_disable]
        # Alerte email synthétique
        subject = "[DIA-Core] Surcharge détectée — réduction du périmètre"
        body = (
            "Surcharge soutenue détectée (" + (decision.reason or "") + ")\n"
            f"Paires actives: {len(active_pairs)} → {len(new_list)} (−{decision.drop_pairs})\n"
            f"Paires désactivées: {to_disable}\n"
            "Action requise: vérifier optimisation ou augmenter la capacité.\n"
        )
        try:
            self.alerter.send(subject, body)
        except Exception:
            # On ne fait pas échouer l'exécution si l'email tombe en erreur
            pass
        return new_list