#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/dia-core"
APP_USER="dia"
SERVICE="dia-core"
VENV="$APP_DIR/.venv"
CONFIG="$APP_DIR/Config/config.json"
ENVFILE="$APP_DIR/.env"
LOG_DIR="/var/log/dia-core"

_red()  { printf "\033[31m%s\033[0m\n" "$*"; }
_grn()  { printf "\033[32m%s\033[0m\n" "$*"; }
_yel()  { printf "\033[33m%s\033[0m\n" "$*"; }
_fail() { _red "✗ $*"; exit 1; }
_ok()   { _grn "✓ $*"; }

echo "== DIA-Core verify =="

# 0) Binaries
command -v systemctl >/dev/null || _fail "systemctl introuvable"
command -v python3   >/dev/null || _fail "python3 introuvable"

# 1) Dossiers & fichiers
[ -d "$APP_DIR" ] || _fail "$APP_DIR manquant"
[ -d "$VENV"    ] || _fail "$VENV manquant"
[ -d "$LOG_DIR" ] || _fail "$LOG_DIR manquant"
[ -f "$CONFIG"  ] || _fail "$CONFIG manquant"
[ -f "$ENVFILE" ] || _yel  "$ENVFILE manquant (pas bloquant si variables déjà exportées)"

# 2) Ownership
own_app="$(stat -c '%U:%G' "$APP_DIR")"
[ "$own_app" = "$APP_USER:$APP_USER" ] || _fail "Mauvais owner $APP_DIR ($own_app), attendu $APP_USER:$APP_USER"
own_log="$(stat -c '%U:%G' "$LOG_DIR")"
[ "$own_log" = "$APP_USER:$APP_USER" ] || _fail "Mauvais owner $LOG_DIR ($own_log), attendu $APP_USER:$APP_USER"
_ok "Ownership OK"

# 3) Permissions secrets
if [ -f "$ENVFILE" ]; then
  perm="$(stat -c '%a' "$ENVFILE")"
  own_env="$(stat -c '%U:%G' "$ENVFILE")"
  [ "$own_env" = "$APP_USER:$APP_USER" ] || _fail ".env owner ($own_env), attendu $APP_USER:$APP_USER"
  [ "$perm" = "600" ] || _fail ".env permissions $perm, attendu 600"
fi
_ok "Secrets (.env) OK"

# 4) Python / venv
[ -x "$VENV/bin/python" ] || _fail "Python venv introuvable"
pyver="$("$VENV/bin/python" - <<'PY'
import sys; v=sys.version_info
print(f"{v.major}.{v.minor}")
PY
)"
case "$pyver" in
  3.11|3.11.*|3.12|3.12.*|3.13|3.13.*) _ok "Python $pyver OK" ;;
  *) _fail "Python $pyver trop ancien (>=3.11 requis)" ;;
esac

# 5) Config JSON minimale
"$VENV/bin/python" - <<PY || _fail "Config JSON invalide"
import json,sys,os
p=os.environ.get("CONFIG","$CONFIG")
with open(p,"r",encoding="utf-8") as f: j=json.load(f)
for k in ("mode","logging","exchange","risk"):
    assert k in j, f"clé manquante: {k}"
print("config OK")
PY
_ok "Config JSON OK"

# 6) Imports & smoke test Python (sans réseau)
sudo -u "$APP_USER" "$VENV/bin/python" - <<'PY' || exit 1
from dia_core.risk.sizing import SizingParams, compute_position_size
from dia_core.risk.validator import RiskCheckParams, validate_order
from types import SimpleNamespace

# sizing
params = SizingParams(
    equity=1000.0, price=200.0, atr=5.0,
    risk_per_trade_pct=1.0, k_atr=2.0,
    min_qty=0.001, min_notional=10.0, qty_decimals=3
)
qty = compute_position_size(params)
assert qty >= 0.001, "qty sous min_qty"
assert qty*params.price >= params.min_notional, "notionnel sous min_notional"

# validator
limits = SimpleNamespace(
    max_exposure_pct=50.0,
    max_orders_per_min=10,
    max_daily_loss_pct=5.0,
    max_drawdown_pct=10.0,
)
validate_order(limits, RiskCheckParams(
    current_exposure_pct=0.0,
    projected_exposure_pct=10.0,
    daily_loss_pct=0.0,
    drawdown_pct=0.0,
    orders_last_min=0,
))
print("smoke OK")
PY
_ok "Imports/logic OK"

# 7) Service systemd
systemctl cat "$SERVICE" >/dev/null 2>&1 || _fail "Service $SERVICE absent"
is_enabled="$(systemctl is-enabled "$SERVICE" || true)"
is_active="$(systemctl is-active "$SERVICE" || true)"
[ "$is_enabled" = "enabled" ] || _yel "Service non activé (is-enabled=$is_enabled)"
[ "$is_active"  = "active"  ] || _yel "Service non démarré (is-active=$is_active)"

# 8) Derniers logs
echo "--- journalctl (dernieres lignes) ---"
journalctl -u "$SERVICE" -n 50 --no-pager || true
echo "-------------------------------------"

_grn "Vérification terminée."
[ "$is_active" = "active" ] || { _yel "TIP: sudo systemctl restart $SERVICE"; exit 0; }
exit 0
