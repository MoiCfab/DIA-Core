# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : tracking/trade_logger.py

Description :
Responsable de l`enregistrement structuré des ordres exécutés
dans un fichier CSV ou JSON (par défaut : trade_log.jsonl).

Utilisé par :
    - BotEngine (à chaque appel de executor.submit)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from dataclasses import dataclass
from datetime import datetime, UTC
import json
import os
from typing import Any


@dataclass
class TradeLogEntry:
    symbol: str
    action: str  # "buy" ou "sell"
    size: float
    price: float
    status: str  # "executed" (live) ou "simulated" (dry_run)
    meta: dict[str, Any] | None = None  # dict: (facultatif) infos complémentaires


class TradeLogger:
    """Composant simple de suivi des ordres exécutés."""

    def __init__(self, path: str = "logs/trade_log.jsonl") -> None:
        """
        Initialise le logger.

        Args:
          path: str:
            Chemin vers le fichier à écrire (créé si absent)
        """
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def log_trade(self, entry: TradeLogEntry) -> None:
        """
        Enregistre un trade dans le fichier log.

        Args:
          entry : TradeLogEntry

        Returns:
          None
        """
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "symbol": entry.symbol,
            "action": entry.action,
            "size": entry.size,
            "price": entry.price,
            "status": entry.status,
            "meta": entry.meta or {},
        }

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
