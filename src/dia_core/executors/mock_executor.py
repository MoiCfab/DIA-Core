# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : exec/executors/mock_executor.py

Description :
Exécuteur simulé pour les tests ou le mode dry_run.
Ne transmet pas de vrai ordre, mais log l'intention.

Utilisé par :
    - BotEngine
    - Injection via mode_loader

Auteur : DYXIUM Invest / D.I.A. Core
"""

from src.dia_core.models.intent import OrderIntent


class MockExecutor:
    """Exécuteur simulé (dry_run) pour valider la logique du bot."""

    def __init__(self) -> None:
        """Initialise le mock sans état."""
        self.last_order: OrderIntent | None = None  # Enregistre le dernier ordre simulé

    def submit(self, intent: OrderIntent, symbol: str) -> None:
        """
        Simule l'envoi d'un ordre sans exécution réelle.

        Args:
          intent: OrderIntent:
            Intention de trade générée par la policy
          symbol: str:
            Symbole concerné (ex: "BTC/EUR")

        Returns:
          None
        """
        self.last_order = intent
        print(f"[MockExecutor] {symbol} → {intent.action.upper()} @ {intent.size}")
