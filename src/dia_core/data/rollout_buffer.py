# src/dia_core/data/rollout_buffer.py
"""Événements de rollout (décisions et résultats) sérialisés en JSONL."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any
from collections.abc import Mapping


@dataclass(frozen=True)
class RolloutEvent:
    """Événement élémentaire journalisé dans le buffer."""

    ts: int
    phase: str  # "decision" | "outcome"
    symbol: str
    arm_idx: int | None
    info: dict[str, Any]


@dataclass(frozen=True)
class DecisionInfo:
    """Métadonnées d`une décision de stratégie."""

    arm_idx: int
    regime: Mapping[str, float]
    params: Mapping[str, float]
    side: str | None  # "buy" | "sell" | None


class RolloutBuffer:
    """Buffer JSONL léger pour tracer (R, action, récompense)."""

    def __init__(self, path: str | Path = "Logs/rollouts.jsonl") -> None:
        """Initialise le buffer et crée le dossier au besoin."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: RolloutEvent) -> None:
        """Ajoute un événement sérialisé en fin de fichier."""
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    def log_decision(self, *, symbol: str, meta: DecisionInfo) -> None:
        """Journalise une décision de stratégie."""
        self.append(
            RolloutEvent(
                ts=int(time.time()),
                phase="decision",
                symbol=symbol,
                arm_idx=meta.arm_idx,
                info={"regime": dict(meta.regime), "params": dict(meta.params), "side": meta.side},
            )
        )

    def log_outcome(self, *, symbol: str, arm_idx: int, reward: float) -> None:
        """Journalise le résultat associé à une décision antérieure."""
        self.append(
            RolloutEvent(
                ts=int(time.time()),
                phase="outcome",
                symbol=symbol,
                arm_idx=arm_idx,
                info={"reward": reward},
            )
        )
