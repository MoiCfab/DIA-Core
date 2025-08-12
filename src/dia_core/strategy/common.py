"""Types et constantes partagés entre stratégies pour éviter les imports circulaires."""

from __future__ import annotations
from dataclasses import dataclass

# === Déplacer ici, à l'identique, les constantes aujourd'hui dans adaptive_trade.py ===
_MOMENTUM_BUY_THRESHOLD: float = 0.5
_MOMENTUM_SELL_THRESHOLD: float = 0.0


# === Déplacer ici la définition exacte d'AdaptiveParams depuis adaptive_trade.py ===
@dataclass(frozen=True)
class AdaptiveParams:
    """Paramètres simples de modulation.

    Attributes :
        base_prob : probabilité de base (régime neutre)
        max_boost : amplification max de la prob par score
        k_atr_min : k_atr en régime calme
        k_atr_max : k_atr en régime explosif

    Args:

    Returns:

    """

    base_prob: float = 0.10
    max_boost: float = 0.60
    k_atr_min: float = 1.5
    k_atr_max: float = 3.0
