# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : risk/risk_manager.py

Description :
Composant responsable du dimensionnement des positions
en fonction de la volatilité, de l`équité, et des paramètres de sécurité.

Utilisé par :
    BotEngine (avant exécution d`un ordre)
    Peut être enrichi avec IA plus tard

Auteur : DYXIUM Invest / D.I.A. Core
"""

import pandas as pd


class RiskManager:
    """Gestionnaire de risque simple basé sur capital et ATR."""

    def __init__(self, capital: float, risk_per_trade: float = 0.01) -> None:
        """
        Initialise le manager.

        Args:
          capital: float:
            Capital global actuel
          risk_per_trade: float:
            Risque maximum autorisé par trade (ex: 0.01 = 1%)
        """
        self.capital = capital
        self.risk_per_trade = risk_per_trade

    def compute_size(self, ohlc: pd.DataFrame) -> float:
        """
        Calcule une taille de position en fonction du risque.

        Args:
          ohlc: pd.DataFrame:
            Données OHLC récentes

        Returns:
          float: Taille de la position en unité base (ex: BTC)
        """
        # Approximation via ATR-like
        ohlc["range"] = ohlc["high"] - ohlc["low"]
        avg_range = ohlc["range"].rolling(14).mean().iloc[-1]

        if avg_range == 0 or pd.isna(avg_range):
            return 0.0

        risk_amount = self.capital * self.risk_per_trade
        position_size: float = risk_amount / avg_range

        return round(position_size, 6)
