#!/usr/bin/env bash
set -euo pipefail

# 0) vérifs de base
command -v python3 >/dev/null || { echo "python3 manquant"; exit 1; }

# 1) utilisateur dédié sans shell
id dia >/dev/null 2>&1 || sudo useradd -r -m -d /home/dia -s /usr/sbin/nologin dia

# 2) déploiement code
sudo mkdir -p /opt/dia-core
sudo cp -a . /opt/dia-core/

# 3) venv + deps
sudo -u dia python3 -m venv /opt/dia-core/.venv
sudo -u dia /opt/dia-core/.venv/bin/pip install -U pip wheel
if [ -f /opt/dia-core/requirements.txt ]; then
  sudo -u dia /opt/dia-core/.venv/bin/pip install -r /opt/dia-core/requirements.txt
else
  # fallback si requirements non présent
  sudo -u dia /opt/dia-core/.venv/bin/pip install pydantic httpx pytest ruff mypy
fi

# 4) config + logs
sudo mkdir -p /opt/dia-core/Config /var/log/dia-core /opt/dia-core/scripts
[ -f /opt/dia-core/Config/config.json ] || sudo cp /opt/dia-core/Config/config.example.json /opt/dia-core/Config/config.json || true

# 5) scripts
sudo install -m 755 /opt/dia-core/scripts/run_bot.sh /opt/dia-core/scripts/run_bot.sh

# 6) service
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

# 7) permissions strictes
sudo chown -R dia:dia /opt/dia-core /var/log/dia-core
sudo chmod -R o-rwx /opt/dia-core
[ -f /opt/dia-core/.env ] && sudo chown dia:dia /opt/dia-core/.env && sudo chmod 600 /opt/dia-core/.env || true

# 8) activer le service
sudo systemctl daemon-reload
sudo systemctl enable --now dia-core.service
sudo systemctl status dia-core.service --no-pager