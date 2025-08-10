#!/usr/bin/env bash
# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited
#
# Nom du script : scripts/run_bot.sh
#
# Description :
#   Script d'exécution du bot DIA-Core.
#   - Definit les chemins principaux (application, venv, config, logs).
#   - Cree le dossier de logs si necessaire.
#   - Active l'environnement virtuel Python.
#   - Lance le bot avec le fichier de configuration spécifie.
#
# Auteur : DYXIUM Invest / D.I.A. Core
#
set -euo pipefail

# Repertoires et fichiers principaux
APP_DIR="/opt/dia-core"
VENV="$APP_DIR/.venv"
CONFIG_PATH="$APP_DIR/Config/config.json"
LOG_DIR="/var/log/dia-core"

# Creation du dossier de logs si absent
mkdir -p "$LOG_DIR"

# Activation de l'environnement virtuel
source "$VENV/bin/activate"

# Lancement du bot avec la configuration spécifique
exec python -m dia_core.cli.main --config "$CONFIG_PATH"
