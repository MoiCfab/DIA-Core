"""Module src/dia_core/data/rollout_buffer.py."""

# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any


@dataclass(frozen=True)
class RolloutEvent:
    """Buffer d`événements pour journaliser décisions et résultats."""

    ts: int
    phase: str  # "decision" | "outcome"
    symbol: str
    arm_idx: int | None
    info: dict[str, Any]


class RolloutBuffer:
    """Buffer JSONL très léger pour tracer (R, action, récompense)."""

    def __init__(self, path: str | Path = "Logs/rollouts.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: RolloutEvent) -> None:
        """

        Args:
          event: RolloutEvent:
          event: RolloutEvent:

        Returns:

        """
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    # Helpers pratiques
    def log_decision(
        self,
        *,
        symbol: str,
        arm_idx: int,
        regime: dict[str, float],
        params: dict[str, float],
        side: str | None,
    ) -> None:  # pylint: disable=too-many-arguments
        """Args:
          *:
          symbol: str:
          arm_idx: int:
          regime: dict[str:
          float]:

        Args:
          side: str
          *:
          symbol: str:
          arm_idx: int:
          regime: dict[str:
          float]:
          params: dict[str:
          side: str | None:

        Returns:


        """
        self.append(
            RolloutEvent(
                ts=int(time.time()),
                phase="decision",
                symbol=symbol,
                arm_idx=arm_idx,
                info={"regime": regime, "params": params, "side": side},
            )
        )

    def log_outcome(self, *, symbol: str, arm_idx: int, reward: float) -> None:
        """

        Args:
          *:
          symbol: str:
          arm_idx: int:
          reward: float:
          symbol: str:
          arm_idx: int:
          reward: float:

        Returns:

        """
        self.append(
            RolloutEvent(
                ts=int(time.time()),
                phase="outcome",
                symbol=symbol,
                arm_idx=arm_idx,
                info={"reward": reward},
            )
        )
