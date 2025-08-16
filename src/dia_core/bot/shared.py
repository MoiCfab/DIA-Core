# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : bot/shared.py

Description :
Contient la structure d'état global partagé entre les moteurs du bot.
Permet de suivre l'exposition cumulée, le drawdown, le capital utilisé, etc.

Utilisé par :
    BotEngine (lecture + écriture)
    Orchestrator (contrôle global)
    ResourceManager (limitation de charge)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class SharedState:
    """État partagé entre tous les moteurs DIA-Core."""

    global_equity: float  # Capital global initial ou courant
    max_drawdown_pct: float = 0.25  # Drawdown maximum autorisé (25% par défaut)

    exposure_by_symbol: dict[str, float] = field(default_factory=dict)  # Exposition par paire
    equity_used: float = 0.0  # Montant total actuellement engagé
    current_drawdown_pct: float = 0.0  # Drawdown courant calculé

    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def update_exposure(self, symbol: str, exposure: float) -> None:
        """
        Met à jour l'exposition d'un symbole donné.

        Args:
          symbol: str:
            Le symbole (ex: "BTC/EUR")
          exposure: float:
            L'exposition actuelle (0.0 à 1.0 max)
        """
        with self._lock:
            self.exposure_by_symbol[symbol] = exposure
            self.equity_used = sum(self.exposure_by_symbol.values()) * self.global_equity

    def can_trade(self, symbol: str, threshold: float = 0.2) -> bool:
        """
        Vérifie si un symbole peut être (re)tradé sans dépasser l'exposition globale.

        Args:
          symbol: str:
            Le symbole concerné
          threshold: float:
            Seuil maximum global autorisé (ex: 0.2 = 20%)

        Returns:
          bool: True si tradable, False sinon
        """
        _ = symbol
        with self._lock:
            total_expo = sum(self.exposure_by_symbol.values())
            return total_expo + threshold <= 1.0

    def record_drawdown(self, equity_now: float) -> None:
        """
        Met à jour le drawdown courant par rapport à l'équité de départ.

        Args:
          equity_now: float:
            Valeur courante estimée du portefeuille

        Returns:
          None
        """
        with self._lock:
            drawdown = 1.0 - (equity_now / self.global_equity)
            self.current_drawdown_pct = max(self.current_drawdown_pct, drawdown)
