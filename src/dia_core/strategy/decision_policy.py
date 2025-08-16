# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : strategy/decision_policy.py

Description :
Contrat de politique de décision pour DIA-Core.

Auteur : DYXIUM Invest / D.I.A. Core
"""

from typing import Literal, Protocol, runtime_checkable
import pandas as pd

TradeDecision = Literal["buy", "sell", "hold"]


@runtime_checkable
class DecisionPolicy(Protocol):
    """Interface commune des politiques de décision."""

    def decide(
        self, symbol: str, window: pd.DataFrame, regime: dict[str, float]
    ) -> TradeDecision: ...
