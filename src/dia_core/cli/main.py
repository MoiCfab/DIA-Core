# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : cli/main.py

Description :
Point d'entrée principal de DIA-Core. Ce fichier ne contient
aucune logique métier. Il initialise le contrôleur d'exécution
central ('ExecutionController') avec le mode fourni en argument,
puis délègue entièrement la gestion au contrôleur.

Utilisé par :
    Interface CLI (lancement en cron ou manuel)
    Environnement shell / script / service

Auteur : DYXIUM Invest / D.I.A. Core
"""

import sys

from src.dia_core.controller.execution import ExecutionController

MIN_ARGS_REQUIRED = 2  # 1 = script, 2 = script + mode


def main(mode: str) -> None:
    """
    Lance le bot en fonction du mode spécifié.

    Ce point d`entrée est volontairement minimaliste :
    il délègue à 'ExecutionController' la responsabilité
    de construire les composants nécessaires.

    Args :
      mode : str :
        Mode d`exécution à lancer. Doit être l`un des suivants :
        - "live"
        - "dry_run"
        - "backtest"

    Returns :
      None
    """
    controller = ExecutionController(mode)
    controller.run()


if __name__ == "__main__":
    # On lit le mode passé en argument
    if len(sys.argv) < MIN_ARGS_REQUIRED:
        print("Usage : python main.py <mode>")
        print("Exemples : live, dry_run, backtest")
        sys.exit(1)

    mode_arg = sys.argv[1]
    main(mode_arg)
