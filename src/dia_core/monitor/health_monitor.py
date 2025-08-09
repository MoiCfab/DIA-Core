from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Sequence

try:
    import psutil  # type: ignore
except Exception:  # fail soft si non installé
    psutil = None


@dataclass
class LoadSnapshot:
    ts: float
    cpu_pct: float
    ram_pct: float
    latency_ms: float  # latence moyenne du cycle stratégie (optionnel)


@dataclass
class Thresholds:
    cpu_pct: float = 90.0
    ram_pct: float = 90.0
    latency_ms: float = 250.0
    sustain_windows: int = 3  # nb d'échantillons consécutifs nécessaires pour alerte


@dataclass
class OverloadDecision:
    overloaded: bool
    reason: str | None
    drop_pairs: int  # combien de paires non prioritaires désactiver


class HealthMonitor:
    """Sonde ultra-légère pour surveiller la charge et décider d'une réduction de périmètre.

    - Collecte CPU/RAM avec psutil si dispo; sinon CPU=RAM=0.
    - Prend en entrée une latence moyenne (ms) mesurée par l'orchestrateur.
    - Applique un critère de dépassement soutenu (hystérésis simple).
    """

    def __init__(self, thresholds: Thresholds, sample_period_s: float = 30.0) -> None:
        self.th = thresholds
        self.sample_period_s = sample_period_s
        self._history: list[LoadSnapshot] = []
        self._violation_streak = 0

    def sample(self, latency_ms: float = 0.0) -> LoadSnapshot:
        now = time.time()
        cpu = psutil.cpu_percent(interval=None) if psutil else 0.0
        ram = psutil.virtual_memory().percent if psutil else 0.0
        snap = LoadSnapshot(ts=now, cpu_pct=cpu, ram_pct=ram, latency_ms=latency_ms)
        self._history.append(snap)
        # garder taille raisonnable
        if len(self._history) > 128:
            self._history = self._history[-128:]
        return snap

    def evaluate(self, active_pairs: Sequence[str], low_priority: Sequence[str]) -> OverloadDecision:
        if not self._history:
            return OverloadDecision(False, None, 0)
        s = self._history[-1]
        violated = (s.cpu_pct >= self.th.cpu_pct) or (s.ram_pct >= self.th.ram_pct) or (s.latency_ms >= self.th.latency_ms)
        if violated:
            self._violation_streak += 1
        else:
            self._violation_streak = 0
        if self._violation_streak >= self.th.sustain_windows:
            # Règle simple: désactiver jusqu'à 20% des paires, min 1, selon la liste low_priority
            n_active = max(1, len(active_pairs))
            to_drop = max(1, int(0.2 * n_active))
            to_drop = min(to_drop, len(low_priority))
            reason = f"cpu={s.cpu_pct:.1f}% ram={s.ram_pct:.1f}% lat={s.latency_ms:.0f}ms"
            return OverloadDecision(True, reason, to_drop)
        return OverloadDecision(False, None, 0)