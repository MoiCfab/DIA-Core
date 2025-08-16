# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : orchestrator/orchestrator.py

Description :
Supervise l'exécution temps réel du bot (live/dry_run).
Gère le scan du marché, les ressources disponibles,
et distribue les tâches aux moteurs de trading (BotEngine).

Utilisé par :
    controller/execution.py

Auteur : DYXIUM Invest / D.I.A. Core
"""

from dataclasses import dataclass

from src.dia_core.config.models import BotConfig
from src.dia_core.bot.shared import SharedState
from src.dia_core.strategy.decision_policy import DecisionPolicy
from src.dia_core.orchestrator.resource_manager import ResourceManager
from src.dia_core.orchestrator.market_scanner import MarketScanner


@dataclass
class OrchestratorDeps:
    engine_cls: type  # Classe moteur (ex: BotEngine)
    provider_cls: type  # Fournisseur de données (ex : KrakenProvider)
    executor_cls: type  # Exécuteur d`ordres (ex: RealExecutor)
    policy: DecisionPolicy  # Politique de décision (heuristique ou IA)
    shared: SharedState  # État partagé entre les moteurs (DD global, exposition…)


class Orchestrator:
    """Orchestrateur principal pour les modes live/dry_run."""

    def __init__(
        self,
        config: BotConfig,
        deps: OrchestratorDeps,
    ) -> None:
        """
        Initialise l'orchestrateur avec les composants injectés.

        Args :
          config : BotConfig :
            Configuration complète du bot.
          deps : OrchestratorDeps :
            dataclass (ex : BotEngine, kraken, etc.)
        """
        self.config = config  # Configuration globale du bot (mode, capital, options)
        self.engine_cls = deps.engine_cls  # Moteur de trading (BotEngine injecté)
        self.provider_cls = deps.provider_cls  # Source de données (Kraken, etc.)
        self.executor_cls = deps.executor_cls  # Exécuteur (dry_run, réel)
        self.policy = deps.policy  # Politique décisionnelle (heuristique ou IA)
        self.shared = deps.shared  # État partagé entre moteurs

        self.scanner = MarketScanner()  # Composant IA de sélection des symboles
        self.resources = ResourceManager()  # Gestionnaire des ressources système / capital

    def run(self) -> None:
        """
        Exécute un cycle complet d'orchestration.

        Returns :
          None
        """
        # 1. Récupération des symboles éligibles (scanner dynamique ou statique)
        universe = self.scanner.get_symbols()

        # 2. Boucle principale : évalue chaque symbole indépendamment
        for symbol in universe:

            # 3. Vérifie si les ressources disponibles permettent de traiter ce symbole
            if not self.resources.can_run(symbol, self.shared):
                continue  # Trop de charge ou drawdown → on saute

            # 4. Crée un provider de données pour ce symbole
            provider = self.provider_cls(symbol)

            # 5. Crée un exécuteur adapté au mode (dry_run, réel)
            executor = self.executor_cls()

            # 6. Initialise un moteur de décision/trading pour ce symbole
            engine = self.engine_cls(
                symbol=symbol,
                config=self.config,
                policy=self.policy,
                shared=self.shared,
            )

            # 7. Exécute un tick de trading pour ce symbole
            engine.run_one_tick(provider, executor)
