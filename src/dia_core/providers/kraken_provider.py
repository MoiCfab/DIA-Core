# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : data/providers/kraken_provider.py

Description :
Fournisseur de données temps réel via l'API publique de Kraken.
Transforme les réponses REST en DataFrame OHLC.

Utilisé par :
    - BotEngine
    - Injection live via mode_loader.py

Auteur : DYXIUM Invest / D.I.A. Core
"""

import requests
import pandas as pd
from typing import Literal


def compute_regime(ohlc: pd.DataFrame) -> dict[str, float]:
    """
    Calcule un vecteur de régime simplifié depuis OHLC.

    Args:
      ohlc: pd.DataFrame:

    Returns:
      dict: avec les clés : momentum, trend, volatility
    """
    momentum = (ohlc["close"].iloc[-1] - ohlc["close"].iloc[-5]) / ohlc["close"].iloc[-5]
    volatility = ohlc["close"].pct_change().rolling(5).std().iloc[-1]
    trend = ohlc["close"].rolling(10).mean().iloc[-1] - ohlc["close"].mean()

    return {
        "momentum": float(momentum),
        "volatility": float(volatility),
        "trend": float(trend),
    }


class KrakenProvider:
    """Provider Kraken : données en temp réel OHLC pour un symbole."""

    def __init__(self, symbol: str) -> None:
        """
        Initialise le provider.

        Args:
          symbol: str:
            Paire ex: "BTC/EUR" → converti en "XBTEUR"
        """
        self.symbol = symbol.upper().replace("/", "")
        self.endpoint = "https://api.kraken.com/0/public/OHLC"

    def get_ohlc(self, symbol: str, timeframe: Literal["1m", "5m", "15m"] = "5m") -> pd.DataFrame:
        """
        Récupère les données OHLC pour le symbole depuis Kraken.

        Args:
          symbol: str:
            Symbole ex: "BTC/EUR"
          timeframe: str:
            Résolution (Kraken : 1, 5, 15, 60...)

        Returns:
          pd.DataFrame: Colonnes standard : open, high, low, close, volume
        """
        _ = symbol
        params = {
            "pair": self.symbol,
            "interval": str(int(timeframe.replace("m", ""))),  # converti en str explicitement
        }

        response = requests.get(self.endpoint, params=params, timeout=5)
        data = response.json()

        if not data.get("result"):
            raise RuntimeError(f"Erreur API Kraken : {data}")

        result = next(v for k, v in data["result"].items() if k != "last")
        df = pd.DataFrame(
            result, columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
        )
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)

        df = df.astype(
            {"open": float, "high": float, "low": float, "close": float, "volume": float}
        )

        return df[["open", "high", "low", "close", "volume"]]
