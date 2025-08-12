"""Module src/dia_core/strategy/policy/bandit.py."""

# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import time
from typing import Any, Final

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ArmConfig:
    """Hyperparamètres d'une 'posture' de la stratégie adaptative."""

    base_prob: float
    max_boost: float
    k_atr_min: float
    k_atr_max: float


@dataclass
class BanditPolicy:
    """Bandit bayésien (Thompson sampling) non-contextuel, à bras discrets.
    Récompense ∈ R (PnL/équité, etc.) est ramenée dans [0,1] via tanh.
    Persistance JSON sur disque (Logs/policy.json par défaut).

    Args:

    Returns:

    """

    arms: list[ArmConfig]
    alpha: NDArray[np.float64] = field(default_factory=lambda: np.ones(3, dtype=np.float64))
    beta: NDArray[np.float64] = field(default_factory=lambda: np.ones(3, dtype=np.float64))
    epsilon: float = 0.05  # exploration minimale
    reward_scale: float = 0.01  # ~1% de PnL -> reward ~ 0.73
    storage_path: Path = Path("Logs/policy.json")

    _MIN_AB: Final[float] = 1e-3

    @staticmethod
    def default(storage: str | None = None) -> BanditPolicy:
        """

        Args:
          storage: str | None:  (Default value = None)

        Returns:

        """
        arms = [
            # Calme
            ArmConfig(base_prob=0.05, max_boost=0.35, k_atr_min=1.2, k_atr_max=2.0),
            # Neutre
            ArmConfig(base_prob=0.10, max_boost=0.60, k_atr_min=1.5, k_atr_max=3.0),
            # Agressif
            ArmConfig(base_prob=0.15, max_boost=0.80, k_atr_min=1.8, k_atr_max=3.8),
        ]
        return BanditPolicy(
            arms=arms,
            alpha=np.ones(len(arms), dtype=float),
            beta=np.ones(len(arms), dtype=float),
            storage_path=Path(storage) if storage else Path("Logs/policy.json"),
        )

    # ---------- API principale ----------

    def select(self, rng: np.random.Generator | None = None) -> tuple[int, dict[str, float]]:
        """Tire un bras via Thompson sampling, avec epsilon-exploration.

        Args:
          rng: np.random.Generator | None:  (Default value = None)

        Returns:

        """
        rng = rng or np.random.default_rng()
        if rng.random() < float(self.epsilon):
            idx = int(rng.integers(0, len(self.arms)))
        else:
            # Beta(alpha, beta) ~ proba de 'succès' attendue
            samples = rng.beta(self.alpha.clip(self._MIN_AB), self.beta.clip(self._MIN_AB))
            idx = int(np.argmax(samples))
        arm = self.arms[idx]
        return idx, {
            "base_prob": float(arm.base_prob),
            "max_boost": float(arm.max_boost),
            "k_atr_min": float(arm.k_atr_min),
            "k_atr_max": float(arm.k_atr_max),
        }

    def update(self, arm_idx: int, reward: float) -> None:
        """Met à jour alpha/beta à partir d'une récompense réelle (PnL relatif).
        reward ∈ R → p = 0..1 via 0.5*(1+tanh(reward/scale)).

        Args:
          arm_idx: int:
          reward: float:

        Returns:

        """
        p = float(0.5 * (1.0 + math.tanh(reward / self.reward_scale)))
        self.alpha[arm_idx] += p
        self.beta[arm_idx] += 1.0 - p
        self.save()

    # ---------- Persistance ----------

    def save(self) -> None:
        """ """
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "arms": [arm.__dict__ for arm in self.arms],
            "alpha": self.alpha.tolist(),
            "beta": self.beta.tolist(),
            "epsilon": self.epsilon,
            "reward_scale": self.reward_scale,
            "ts": int(time.time()),
        }
        self.storage_path.write_text(json.dumps(data), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> BanditPolicy:
        """

        Args:
          path: str | Path:

        Returns:

        """
        p = Path(path)
        if not p.exists():
            return cls.default(str(p))
        js = json.loads(p.read_text(encoding="utf-8"))
        arms = [ArmConfig(**a) for a in js["arms"]]
        return cls(
            arms=arms,
            alpha=np.asarray(js["alpha"], dtype=float),
            beta=np.asarray(js["beta"], dtype=float),
            epsilon=float(js.get("epsilon", 0.05)),
            reward_scale=float(js.get("reward_scale", 0.01)),
            storage_path=p,
        )
