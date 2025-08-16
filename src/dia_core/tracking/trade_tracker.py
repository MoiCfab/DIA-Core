# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : tracking/trade_tracker.py

Description :
Composant d`analyse post-trade : calcule PnL, performances,
nombre de trades gagnants/perdants, drawdown, etc.

Utilisé par :
    - Analyse manuelle
    - Mode backtest (plus tard)

Auteur : DYXIUM Invest / D.I.A. Core
"""

import json
from typing import Any
import pandas as pd


class TradeTracker:
    """Analyseur de performance basé sur le fichier de log de trades."""

    def __init__(self, path: str = "logs/trade_log.jsonl") -> None:
        self.path = path
        self.trades: list[dict[str, Any]] = self._load()

    def _load(self) -> list[dict[str, Any]]:
        """Charge le fichier de logs."""
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def to_dataframe(self) -> pd.DataFrame:
        """Retourne-les trades sous forme de DataFrame."""
        return pd.DataFrame(self.trades)

    def summary(self) -> dict[str, Any]:
        """
        Calcule un résumé statistique global.

        Returns:
          dict: PnL global, trades gagnants, taux réussite, etc.
        """
        df = self.to_dataframe()
        stats: dict[str, Any] = {}

        if df.empty:
            return {"status": "no data"}

        df["pl"] = df["size"] * df["price"] * df["action"].map({"buy": -1, "sell": 1})
        df["cum_pl"] = df["pl"].cumsum()
        df["drawdown"] = df["cum_pl"].cummax() - df["cum_pl"]

        stats["total_trades"] = len(df)
        stats["total_pnl"] = round(df["pl"].sum(), 2)
        stats["max_drawdown"] = round(df["drawdown"].max(), 2)
        stats["average_trade"] = round(df["pl"].mean(), 2)

        stats["by_symbol"] = {
            sym: round(pl, 2) for sym, pl in df.groupby("symbol")["pl"].sum().items()
        }

        return stats
