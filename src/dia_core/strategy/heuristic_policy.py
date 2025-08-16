# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : strategy/heuristic_policy.py

Description :
Politique heuristique simple basée sur un score continu.

Auteur : DYXIUM Invest / D.I.A. Core
"""

from dataclasses import dataclass
from typing import Final
import pandas as pd
from .decision_policy import DecisionPolicy, TradeDecision


@dataclass(frozen=True, slots=True)
class HeuristicWeights:
    momentum: float = 1.0
    volatility: float = 0.5
    trend: float = 0.8


class HeuristicPolicy(DecisionPolicy):
    POS_TH: Final[float] = 0.6
    NEG_TH: Final[float] = -0.6

    def __init__(self, weights: HeuristicWeights | None = None) -> None:
        self._w = weights or HeuristicWeights()

    @staticmethod
    def _clip(x: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, x))

    def _score(self, regime: dict[str, float]) -> float:
        m = self._clip(regime.get("momentum", 0.0), -2.0, 2.0)
        v = self._clip(regime.get("volatility", 0.0), 0.0, 2.0)
        t = self._clip(regime.get("trend", 0.0), -2.0, 2.0)
        vol_penalty = 1.0 - (v / 2.0)
        return (self._w.momentum * m + self._w.trend * t) * (0.5 + 0.5 * vol_penalty)

    def decide(self, symbol: str, window: pd.DataFrame, regime: dict[str, float]) -> TradeDecision:
        s = self._score(regime)
        if s >= self.POS_TH:
            return "buy"
        if s <= self.NEG_TH:
            return "sell"
        return "hold"
