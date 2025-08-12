"""Module src/dia_core/cli/calibrate.py."""

# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from dia_core.strategy.policy.bandit import BanditPolicy


def main(argv: list[str] | None = None) -> int:
    """

    Args:
      argv: list[str] | None:  (Default value = None)
      argv: list[str] | None:  (Default value = None)

    Returns:

    """
    parser = argparse.ArgumentParser("dia-core-calibrate")
    parser.add_argument("--policy", default="Logs/policy.json")
    parser.add_argument("--rollouts", default="Logs/rollouts.jsonl")
    args = parser.parse_args(argv)

    pol = BanditPolicy.load(args.policy)

    # Recalibrage simple depuis rollouts (moyenne des rewards par bras)
    path = Path(args.rollouts)
    if path.exists():
        sums = [0.0] * len(pol.arms)
        cnts = [0] * len(pol.arms)
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                js: dict[str, Any] = json.loads(line)
                if js.get("phase") != "outcome":
                    continue
                i = int(js.get("arm_idx", -1))
                info = js.get("info") or {}
                r = float(info.get("reward", 0.0))
                if 0 <= i < len(pol.arms):
                    sums[i] += r
                    cnts[i] += 1
            except (JSONDecodeError, TypeError, ValueError, KeyError):
                continue

        for i, c in enumerate(cnts):
            if c > 0:
                avg = sums[i] / max(1, c)
                pol.update(i, avg)

    pol.save()
    print(f"Calibrated policy saved to: {pol.storage_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
