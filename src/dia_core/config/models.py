# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : config/models.py

Description :
Définit les modèles de configuration centrale utilisés dans l'orchestrateur,
y compris la structure principale 'BotConfig'.

Utilisé par :
    ExecutionController
    Orchestrator
    BacktestEngine

Auteur : DYXIUM Invest / D.I.A. Core
"""

from dataclasses import dataclass


@dataclass
class BotConfig:
    """Contient la configuration globale du bot selon le mode."""

    mode: str  # "live", "dry_run", "backtest"
    symbols: list[str] | None = None  # Symboles à forcer (si défini)
    initial_equity: float = 100_000.0
    dynamic_risk: bool = True
    data_path: str | None = None  # Pour mode backtest
    log_level: str = "INFO"
