# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : data/providers/mock_provider.py

Description :
Fournisseur de données OHLC factice pour tests unitaires ou dry_run.
Génère des données aléatoires et un vecteur de régime synthétique.

Utilisé par :
    - BotEngine
    - Injection via mode_loader

Auteur : DYXIUM Invest / D.I.A. Core
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, UTC
from typing import Literal


def get_ohlc(symbol: str, timeframe: Literal["5m", "1h"] = "5m") -> pd.DataFrame:
    """
    Retourne une DataFrame OHLC simulée.

    Args:
      symbol: str:
        Le symbole demandé
      timeframe: str:
        Résolution des données ("5m" ou "1h")

    Returns:
      pd.DataFrame: Données OHLC récentes
    """
    _ = symbol
    now = datetime.now(tz=UTC)

    period = 60 if timeframe == "1h" else 5
    index = [now - timedelta(minutes=i * period) for i in reversed(range(100))]

    prices = np.cumsum(np.random.randn(100)) + 100
    data = pd.DataFrame(
        {
            "open": prices + np.random.randn(100) * 0.2,
            "high": prices + np.random.rand(100) * 0.5,
            "low": prices - np.random.rand(100) * 0.5,
            "close": prices,
            "volume": np.random.randint(100, 1000, size=100),
        },
        index=index,
    )

    return data


def compute_regime(ohlc: pd.DataFrame) -> dict[str, float]:
    """
    Génère un vecteur de régime synthétique.

    Args:
      ohlc: pd.DataFrame:
        Les données à analyser

    Returns:
      dict: vecteur R (ex: tendance, momentum, etc.)
    """
    momentum = (ohlc["close"].iloc[-1] - ohlc["close"].iloc[-5]) / ohlc["close"].iloc[-5]
    volatility = ohlc["close"].pct_change().rolling(5).std().iloc[-1]
    trend = ohlc["close"].rolling(10).mean().iloc[-1] - ohlc["close"].mean()

    return {
        "momentum": float(momentum),
        "volatility": float(volatility),
        "trend": float(trend),
    }


class MockProvider:
    """Provider simulé générant des données OHLC aléatoires."""

    def __init__(self, symbol: str) -> None:
        """
        Initialise le provider pour une paire donnée.

        Args:
          symbol: str:
            Le symbole à simuler (ex: "BTC/EUR")
        """
        self.symbol = symbol
