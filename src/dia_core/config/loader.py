# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : config/loader.py

Description :
Contient la logique de chargement de configuration en fonction du mode.

Utilisé par :
    ExecutionController

Auteur : DYXIUM Invest / D.I.A. Core
"""

from src.dia_core.config.models import BotConfig


def load_config(mode: str) -> BotConfig:
    """
    Construit un objet de configuration selon le mode choisi.

    Args:
      mode: str:
        Mode d'exécution ("live", "dry_run", "backtest")

    Returns:
      BotConfig
    """
    mode = mode.lower()

    if mode == "backtest":
        return BotConfig(
            mode="backtest",
            symbols=["BTC/EUR"],
            data_path="backtest_data/BTC-EUR.csv",
            initial_equity=10_000.0,
        )

    if mode == "live":
        return BotConfig(
            mode="live",
            symbols=None,  # Laisse le scanneur choisir
            initial_equity=20_000.0,
        )

    return BotConfig(
        mode="dry_run",
        symbols=["BTC/EUR"],
        initial_equity=5_000.0,
    )
