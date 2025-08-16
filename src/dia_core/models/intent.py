# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : models/intent.py

Description :
Représente une intention de trade produite par la stratégie.
Encapsule l'action (buy/sell/hold), la taille et d'autres méta-infos.

Utilisé par :
    - DecisionPolicy (output)
    - BotEngine → Executor (input)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from dataclasses import dataclass, field
from typing import Literal, Any

Action = Literal["buy", "sell", "hold"]


@dataclass
class OrderIntent:
    """Représente une intention de trade standardisée."""

    action: Action
    size: float = 0.0  # Quantité à trader, 0.0 = aucune action
    symbol: str | None = None
    price: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def buy(
        cls,
        size: float,
        symbol: str | None = None,
        price: float | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "OrderIntent":
        return cls(action="buy", size=size, symbol=symbol, price=price, meta=meta or {})

    @classmethod
    def sell(
        cls,
        size: float,
        symbol: str | None = None,
        price: float | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "OrderIntent":
        return cls(action="sell", size=size, symbol=symbol, price=price, meta=meta or {})

    # Aliases conviviaux (évite de casser du code appelant)
    @classmethod
    def long(
        cls,
        size: float,
        symbol: str | None = None,
        price: float | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "OrderIntent":
        return cls.buy(size=size, symbol=symbol, price=price, meta=meta)

    @classmethod
    def short(
        cls,
        size: float,
        symbol: str | None = None,
        price: float | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "OrderIntent":
        return cls.sell(size=size, symbol=symbol, price=price, meta=meta)

    @classmethod
    def hold(cls, symbol: str | None = None, meta: dict[str, Any] | None = None) -> "OrderIntent":
        return cls(action="hold", size=0.0, symbol=symbol, price=0.0, meta=meta or {})

    @classmethod
    def from_prediction(cls, prediction: int | str) -> "OrderIntent":
        """
        Conversion pratique depuis une prédiction IA.
        Args:
          prediction: -1, 0, 1 ou "sell"/"hold"/"buy"
        """
        mapping: dict[int | str, OrderIntent] = {
            -1: cls.short(0.01),
            0: cls.hold(),
            1: cls.long(0.01),
            "sell": cls.short(0.01),
            "hold": cls.hold(),
            "buy": cls.long(0.01),
        }
        result: OrderIntent = mapping.get(prediction, cls.hold())
        return result
