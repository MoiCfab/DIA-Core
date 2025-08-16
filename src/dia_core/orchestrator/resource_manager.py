# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : orchestrator/resource_manager.py

Description :
Gestionnaire de ressources du bot. Permet de limiter la charge
(exposition globale, drawdown, CPU futur...) avant de lancer un moteur.

Utilisé par :
    - orchestrator/orchestrator.py

Auteur : DYXIUM Invest / D.I.A. Core
"""

from src.dia_core.bot.shared import SharedState


class ResourceManager:
    """Gestionnaire de ressources globales pour les moteurs."""

    def __init__(self, max_global_expo: float = 0.3) -> None:
        """
        Initialise les seuils.

        Args:
          max_global_expo: float:
            Exposition maximale globale autorisée (ex: 0.3 = 30%)
        """
        self.max_global_expo = max_global_expo

    def can_run(self, symbol: str, shared: SharedState) -> bool:
        """
        Vérifie si un moteur peut être lancé pour ce symbole.

        Vérifie :
          - que l'exposition globale ne dépasse pas la limite
          - que le drawdown reste dans la marge autorisée

        Args:
          symbol: str:
            Le symbole concerné
          shared: SharedState:
            L'état partagé global du bot

        Returns:
          bool: True si exécutable, False sinon
        """
        if not shared.can_trade(symbol, threshold=self.max_global_expo):
            return False

        return shared.current_drawdown_pct <= shared.max_drawdown_pct
