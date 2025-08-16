# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : bot/bot_engine.py

Description :
Contient le moteur principal de trading unitaire.
Ce moteur applique la stratégie (via policy),
le risk management et lexécution sur un seul symbole.

Utilisé par :
    orchestrator/orchestrator.py

Auteur : DYXIUM Invest / D.I.A. Core
"""
from typing import Any

from src.dia_core.config.models import BotConfig
from src.dia_core.strategy.decision_policy import DecisionPolicy
from src.dia_core.bot.shared import SharedState


class BotEngine:
    """Moteur de décision et d'exécution pour un symbole unique."""

    def __init__(
        self,
        symbol: str,
        config: BotConfig,
        policy: DecisionPolicy,
        shared: SharedState,
    ) -> None:
        """
        Initialise un moteur de décision pour une paire.

        Args:
          symbol: str:
            Le symbole à trader (ex: "BTC/EUR")
          config: BotConfig:
            La configuration du bot
          policy: DecisionPolicy:
            La stratégie adaptative (IA ou heuristique)
          shared: SharedState:
            Létat global partagé avec les autres moteurs
        """
        self.symbol = symbol
        self.config = config
        self.policy = policy
        self.shared = shared

    def run_one_tick(self, provider: Any, executor: Any) -> None:
        """
        Exécute un cycle complet : données → décision → risque → ordre.

        Args:
          provider: Fournisseur de données OHLC pour le symbole
          executor: Exécuteur d'ordre (dry_run, live, etc.)

        Returns:
          None
        """
        # 1. Récupération des données de marché (OHLC)
        ohlc = provider.get_ohlc(self.symbol)

        # 2. Calcul du vecteur de régime
        regime = provider.compute_regime(ohlc)

        # 3. Génération d'une intention de trade via la policy
        intent = self.policy.decide(self.symbol, ohlc, regime)

        # 4. (À venir) Application du risk manager dynamique ici si nécessaire

        # 5. Envoi de l'ordre (réel ou simulé)
        executor.submit(intent, symbol=self.symbol)
