# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : kraken/types.py

Description :
Definit les types et modeles Pydantic utilises pour formaliser les ordres
et leurs statuts dans l'integration Kraken de DIA-Core.

Utilise par :
    exec/pre_trade.py (verifications)
    exec/executor.py (soumission et suivi d'ordres)
    kraken/client.py (construction des payloads)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

# Types litteraux pour clarifier et limiter les valeurs possibles.
Side = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]


class OrderIntent(BaseModel):
    """Representation d'une intention d'ordre avant envoi a l'exchange."""

    symbol: str
    side: Side
    type: OrderType = "limit"
    qty: float
    limit_price: float | None = None
    time_in_force: Literal["GTC", "IOC"] = "GTC"


class SubmittedOrder(BaseModel):
    """Representation d'un ordre apres soumission a l'exchange."""

    client_order_id: str
    exchange_order_id: str | None = None
    status: Literal["accepted", "rejected", "filled", "partially_filled", "pending"] = "pending"
    reason: str | None = None
