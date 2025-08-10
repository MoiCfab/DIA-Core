#!/usr/bin/env bash
# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited
#
# Nom du script : scripts/installe_system.sh
#
# Description :
#   Script d'installation système pour le bot DIA-Core.
#   - Cree un utilisateur dedie sans shell.
#   - Déploie le code source dans /opt/dia-core.
#   - Configure un environnement virtuel Python et installe les dépendances.
#   - Cree les repertoires de configuration et de logs.
#   - Installe les scripts d'exécution.
#   - Cree et active un service systemd pour l'exécution automatique au démarrage.
#
# Auteur : DYXIUM Invest / D.I.A. Core
#
set -euo pipefail

# 0) Verifications de base
command -v python3 >/dev/null || { echo "python3 manquant"; exit 1; }

# 1) Creation d'un utilisateur dedie sans shell
id dia >/dev/null 2>&1 || sudo useradd -r -m -d /home/dia -s /usr/sbin/nologin dia

# 2) Déploiement du code
sudo mkdir -p /opt/dia-core
sudo cp -a . /opt/dia-core/

# 3) Creation de l'environnement virtuel et installation des dépendances
sudo -u dia python3 -m venv /opt/dia-core/.venv
sudo -u dia /opt/dia-core/.venv/bin/pip install -U pip wheel
if [ -f /opt/dia-core/requirements.txt ]; then
  sudo -u dia /opt/dia-core/.venv/bin/pip install -r /opt/dia-core/requirements.txt
else
  # Fallback si requirements.txt absent
  sudo -u dia /opt/dia-core/.venv/bin/pip install pydantic httpx pytest ruff mypy
fi

# 4) Creation des repertoires de configuration et de logs
sudo mkdir -p /opt/dia-core/Config /var/log/dia-core /opt/dia-core/scripts
[ -f /opt/dia-core/Config/config.json ] || sudo cp /opt/dia-core/Config/config.example.json /opt/dia-core/Config/config.json || true

# 5) Installation des scripts utilitaires
sudo install -m 755 /opt/dia-core/scripts/run_bot.sh /opt/dia-core/scripts/run_bot.sh

# 6) Configuration du service systemd
sudo tee /etc/systemd/system/dia-core.service >/dev/null <<'EOF'
[Unit]
Description=DIA-Core trading bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dia
Group=dia
WorkingDirectory=/opt/dia-core
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/dia-core/scripts/run_bot.sh
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 7) Permissions strictes sur les fichiers et dossiers
sudo chown -R dia:dia /opt/dia-core /var/log/dia-core
sudo chmod -R o-rwx /opt/dia-core
[ -f /opt/dia-core/.env ] && sudo chown dia:dia /opt/dia-core/.env && sudo chmod 600 /opt/dia-core/.env || true

# 8) Activation et démarrage du service
sudo systemctl daemon-reload
sudo systemctl enable --now dia-core.service
sudo systemctl status dia-core.service --no-pager
