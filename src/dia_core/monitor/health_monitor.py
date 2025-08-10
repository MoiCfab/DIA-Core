# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : monitor/health_monitor.py

Description :
Sonde legere pour surveiller l'etat de charge CPU/RAM et la latence de traitement,
avec logique de detection d'une surcharge soutenue. Permet de recommander la
desactivation de certaines paires non prioritaires pour maintenir la stabilite
du systeme.

Utilise par :
    orchestrateur ou boucle principale (controle capacite runtime)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass

try:
    import psutil  # type: ignore
except ImportError:  # fail soft si non installe
    psutil = None

MAX_HISTORY = 128


@dataclass
class LoadSnapshot:
    """Instantane de charge mesure a un instant donne.

    Attributes:
        ts: Horodatage en secondes (time.time()).
        cpu_pct: Utilisation CPU en pourcentage.
        ram_pct: Utilisation RAM en pourcentage.
        latency_ms: Latence moyenne observee (ms) pour un cycle de strategie.
    """

    ts: float
    cpu_pct: float
    ram_pct: float
    latency_ms: float


@dataclass
class Thresholds:
    """Seuils de charge et conditions d'alerte.

    Attributes:
        cpu_pct: Pourcentage CPU maximum tolere.
        ram_pct: Pourcentage RAM maximum tolere.
        latency_ms: Latence maximum toleree (ms).
        sustain_windows: Nombre de mesures consecutives depassant les seuils
            necessaire pour declencher une alerte.
    """

    cpu_pct: float = 90.0
    ram_pct: float = 90.0
    latency_ms: float = 250.0
    sustain_windows: int = 3


@dataclass
class OverloadDecision:
    """Decision retournee apres evaluation de la charge.

    Attributes:
        overloaded: True si surcharge detectee.
        reason: Description de la raison de la surcharge.
        drop_pairs: Nombre de paires non prioritaires a desactiver.
    """

    overloaded: bool
    reason: str | None
    drop_pairs: int


class HealthMonitor:
    """Sonde pour surveiller la charge systeme et recommander des reductions de charge.

    - Utilise psutil pour collecter CPU et RAM (0.0 si psutil indisponible).
    - Accepte une mesure externe de latence en ms.
    - Declenche une alerte si un depassement de seuil est constate pendant
      un nombre de cycles consecutifs defini par sustain_windows.
    """

    def __init__(self, thresholds: Thresholds, sample_period_s: float = 30.0) -> None:
        """Initialise la sonde avec des seuils et une periode d'echantillonnage.

        Args:
            thresholds: Seuils de charge CPU/RAM/latence.
            sample_period_s: Intervalle theorique entre deux mesures (secondes).
        """
        self.th = thresholds
        self.sample_period_s = sample_period_s
        self._history: list[LoadSnapshot] = []
        self._violation_streak = 0

    def sample(self, latency_ms: float = 0.0) -> LoadSnapshot:
        """Effectue une mesure de charge et l'ajoute a l'historique.

        Args:
            latency_ms: Latence mesuree par le moteur (optionnel).

        Returns:
            Un objet LoadSnapshot representant la mesure.
        """
        now = time.time()
        cpu = psutil.cpu_percent(interval=None) if psutil else 0.0
        ram = psutil.virtual_memory().percent if psutil else 0.0
        snap = LoadSnapshot(ts=now, cpu_pct=cpu, ram_pct=ram, latency_ms=latency_ms)
        self._history.append(snap)
        # Garde une taille d'historique raisonnable
        if len(self._history) > MAX_HISTORY:
            self._history = self._history[-MAX_HISTORY:]
        return snap

    def evaluate(
        self, active_pairs: Sequence[str], low_priority: Sequence[str]
    ) -> OverloadDecision:
        """Evalue l'etat de charge et determine si une reduction est necessaire.

        Args:
            active_pairs: Liste des paires actuellement actives.
            low_priority: Liste des paires non prioritaires.

        Returns:
            Une instance OverloadDecision avec:
              - overloaded=True si surcharge persistante detectee.
              - reason de l'alerte.
              - drop_pairs = nombre de paires a desactiver.
        """
        if not self._history:
            return OverloadDecision(False, None, 0)

        s = self._history[-1]
        violated = (
            (s.cpu_pct >= self.th.cpu_pct)
            or (s.ram_pct >= self.th.ram_pct)
            or (s.latency_ms >= self.th.latency_ms)
        )

        if violated:
            self._violation_streak += 1
        else:
            self._violation_streak = 0

        if self._violation_streak >= self.th.sustain_windows:
            # Regle simple: desactiver jusqu'a 20% des paires, min 1
            n_active = max(1, len(active_pairs))
            to_drop = max(1, int(0.2 * n_active))
            to_drop = min(to_drop, len(low_priority))
            reason = f"cpu={s.cpu_pct:.1f}% ram={s.ram_pct:.1f}% lat={s.latency_ms:.0f}ms"
            return OverloadDecision(True, reason, to_drop)

        return OverloadDecision(False, None, 0)
