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
    """Representation d'une intention d'ordre avant envoi a l'exchange.

    Attributes:
        symbol: Symbole de la paire (ex: "BTC/EUR").
        side: Cote de l'ordre ("buy" ou "sell").
        type: Type d'ordre ("market" ou "limit").
        qty: Quantite a echanger.
        limit_price: Prix limite (necessaire si type == "limit").
        time_in_force: Politique de validite ("GTC" = Good Till Cancel, "IOC" = Immediate Or Cancel)
    """

    symbol: str
    side: Side
    type: OrderType = "limit"
    qty: float
    limit_price: float | None = None
    time_in_force: Literal["GTC", "IOC"] = "GTC"


class SubmittedOrder(BaseModel):
    """Representation d'un ordre apres soumission a l'exchange.

    Attributes:
        client_order_id: Identifiant genere localement pour tracer l'ordre.
        exchange_order_id: Identifiant attribue par l'exchange (peut etre None en dry_run).
        status: Statut de l'ordre ("accepted", "rejected", "filled", "partially_filled", "pending").
        reason: Raison du rejet ou information supplementaire si applicable.
    """

    client_order_id: str
    exchange_order_id: str | None = None
    status: Literal["accepted", "rejected", "filled", "partially_filled", "pending"] = "pending"
    reason: str | None = None
