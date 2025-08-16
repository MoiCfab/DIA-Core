# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : strategy/model_based_policy.py

Description :
Politique branchée sur un modèle externe (IA/ML).

Auteur : DYXIUM Invest / D.I.A. Core
"""

from typing import Any, Final
import pandas as pd
from .decision_policy import DecisionPolicy, TradeDecision


class ModelBasedPolicy(DecisionPolicy):
    """Politique qui délègue la prédiction à un modèle externe."""

    # Tables de mapping (réduisent la complexité cyclomatique)
    INT_SIGN_TO_DECISION: Final[dict[int, TradeDecision]] = {-1: "sell", 0: "hold", 1: "buy"}
    BUY_TOKENS: Final[frozenset[str]] = frozenset({"buy", "long", "b"})
    SELL_TOKENS: Final[frozenset[str]] = frozenset({"sell", "short", "s"})

    def __init__(self, model: Any) -> None:
        self._model = model

    @staticmethod
    def _signum(n: int) -> int:
        """Renvoie -1, 0 ou 1 selon le signe de n (sans branchement imbriqué)."""
        return (n > 0) - (n < 0)

    def _map_prediction(self, pred: int | str) -> TradeDecision:
        """Mappe la sortie du modèle vers une décision normalisée."""
        if isinstance(pred, int):
            # Réduction des valeurs entières à {-1, 0, 1} puis lookup direct
            return self.INT_SIGN_TO_DECISION.get(self._signum(pred), "hold")

        p = str(pred).strip().lower()
        if p in self.BUY_TOKENS:
            return "buy"
        if p in self.SELL_TOKENS:
            return "sell"
        return "hold"

    def decide(self, symbol: str, window: pd.DataFrame, regime: dict[str, float]) -> TradeDecision:
        try:
            pred = self._model.predict(symbol, window, regime)
        except (ValueError, RuntimeError):
            return "hold"
        return self._map_prediction(pred)
