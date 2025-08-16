# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : controller/mode_loader.py

Description :
Contient la logique de sélection dynamique des composants
(engine, provider, executor) selon le mode de fonctionnement.

Utilisé par :
    ExecutionController

Auteur : DYXIUM Invest / D.I.A. Core
"""

from collections.abc import Callable
from typing import Any

from src.dia_core.bot.bot_engine import BotEngine
from src.dia_core.providers.mock_provider import MockProvider
from src.dia_core.executors.mock_executor import MockExecutor
from src.dia_core.providers.kraken_provider import KrakenProvider
from src.dia_core.executors.kraken_executor import KrakenExecutor


def build_components(
    mode: str,
) -> tuple[Callable[..., Any], Callable[..., Any], Callable[..., Any]]:
    """
    Retourne les classes nécessaires selon le mode choisi.

    Args:
      mode: str:
        Le mode d'exécution : "live", "dry_run", "backtest"

    Returns:
      tuple: (EngineClass, ProviderClass, ExecutorClass)
    """
    mode = mode.lower()
    engine_cls = BotEngine

    if mode == "live":
        return engine_cls, KrakenProvider, KrakenExecutor

    if mode == "dry_run":
        return engine_cls, MockProvider, MockExecutor

    if mode == "backtest":
        return engine_cls, MockProvider, MockExecutor  # remplacé plus tard

    raise ValueError(f"Mode inconnu : {mode}")
