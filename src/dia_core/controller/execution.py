# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : controller/execution.py

Description :
Contrôleur principal d'exécution de DIA-Core. Ce module centralise la logique
de démarrage du bot en fonction du mode choisi (live, dry_run, backtest).
Il prépare la configuration, les composants nécessaires (shared state, policy),
et délègue à l'orchestrateur ou au moteur de backtest.

Utilisé par :
    cli/main.py (point d`entrée du système)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from src.dia_core.config.loader import load_config
from src.dia_core.orchestrator.orchestrator import Orchestrator, OrchestratorDeps
from src.dia_core.backtest.backtest_engine import BacktestEngine
from src.dia_core.bot.shared import SharedState
from src.dia_core.strategy.heuristic_policy import HeuristicPolicy
from src.dia_core.controller.mode_loader import build_components


class ExecutionController:
    """Contrôleur d'exécution unique pour tous les modes (live, dry_run, backtest)."""

    def __init__(self, mode: str) -> None:
        """
        Initialise le contrôleur avec le mode voulu.

        Args:
          mode: str:
            Mode à exécuter : "live", "dry_run" ou "backtest".
        """
        self.mode = mode.lower()
        self.config = load_config(self.mode)
        self.shared_state = SharedState(global_equity=self.config.initial_equity)
        self.policy = HeuristicPolicy()  # À remplacer par IA plus tard

    def run(self) -> None:
        """
        Lance l`exécution en fonction du mode configuré.

        Returns :
          None
        """
        engine_cls, provider_cls, executor_cls = build_components(self.mode)

        if self.config.data_path is None:
            raise ValueError("data_path must be defined for backtest mode.")

        if self.mode == "backtest":
            engine = BacktestEngine(policy=self.policy, data_path=self.config.data_path)
            engine.run()
        else:
            deps = OrchestratorDeps(
                engine_cls=engine_cls.__class__,
                provider_cls=provider_cls.__class__,
                executor_cls=executor_cls.__class__,
                policy=self.policy,
                shared=self.shared_state,
            )

            orchestrator = Orchestrator(
                config=self.config,
                deps=deps,
            )
            orchestrator.run()
