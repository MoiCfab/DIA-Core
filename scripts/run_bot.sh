#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/dia-core"
VENV="$APP_DIR/.venv"
CONFIG_PATH="$APP_DIR/Config/config.json"
LOG_DIR="/var/log/dia-core"

mkdir -p "$LOG_DIR"
source "$VENV/bin/activate"
exec python -m dia_core.cli.main --config "$CONFIG_PATH"