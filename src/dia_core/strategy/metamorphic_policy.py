# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : strategy/metamorphic_policy.py

Description :
Stratégie métamorphe adaptative.

Auteur : DYXIUM Invest / D.I.A. Core
"""

import pandas as pd
from .decision_policy import DecisionPolicy, TradeDecision


class MetamorphicPolicy(DecisionPolicy):
    """Politique adaptative basée sur le vecteur de régime R.

    R = [volatilité, volume, entropie, momentum, spread, tendance, heure, ...]
    """

    POS_TH: float = 0.3
    NEG_TH: float = -0.3

    def decide(self, symbol: str, window: pd.DataFrame, regime: dict[str, float]) -> TradeDecision:
        # Exemple simple d'interpolation continue :
        momentum = regime.get("momentum", 0.0)
        vol = regime.get("volatility", 0.0)

        # probabilité douce : si momentum fort et vol modéré -> buy
        score = momentum * (1.0 - min(vol, 1.0))

        if score > self.POS_TH:
            return "buy"
        if score < self.NEG_TH:
            return "sell"
        return "hold"
