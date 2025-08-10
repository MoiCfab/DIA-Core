# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : tests/test_cli_basic.py

Description :
Test fonctionnel de l'exécution du CLI DIA-Core en mode dry_run.
Utilise un transport HTTP factice (_DummyTransport) pour simuler les
réponses de l'API Kraken sans effectuer de requêtes réseau réelles.

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import httpx
import pytest

# On suppose que le CLI importe KrakenClient depuis dia_core.kraken.client
from dia_core.cli.main import main


class _DummyTransport(httpx.BaseTransport):
    """Transport HTTP factice pour simuler l'API Kraken.

    - Retourne des donnees OHLC minimales pour l'endpoint public OHLC.
    - Retourne une réponse vide, mais valide pour tout autre endpoint.
    """

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        # Repond OK pour OHLC public
        if request.url.path.endswith("/0/public/OHLC"):
            return httpx.Response(
                200, json={"error": [], "result": {"XXBTZEUR": [[1, 2, 3, 4, 5, 6, 7, 8]]}}
            )
        return httpx.Response(200, json={"error": [], "result": {}})


@pytest.mark.parametrize("mode", ["dry_run"])  # on reste hors reseau
def test_cli_runs_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    """Teste que le CLI peut s'exécuter en mode dry_run avec un transport factice.

    Étapes :
        1. Cree une configuration minimale temporaire.
        2. Injecte un transport HTTP factice via monkeypatch pour KrakenClient.
        3. Lance main() avec la configuration et vérifie que le code retour est 0.

    Args :
        tmp_path : Repertoire temporaire fourni par pytest.
        monkeypatch : Fixture pytest pour modifier le comportement des modules.
        mode : Mode de fonctionnement du bot (ici toujours "dry_run").
    """
    # Config minimale temporaire
    cfg_path = tmp_path / "config.json"
    cfg = {
        "mode": mode,
        "logging": {"dir": str(tmp_path / "logs"), "level": "INFO", "filename": "app.log"},
        "exchange": {
            "symbol": "BTC/EUR",
            "price_decimals": 2,
            "qty_decimals": 3,
            "min_qty": 0.001,
            "min_notional": 10.0,
        },
        "risk": {
            "risk_per_trade_pct": 1.0,
            "max_exposure_pct": 50.0,
            "max_orders_per_min": 10,
            "max_daily_loss_pct": 5.0,
            "max_drawdown_pct": 10.0,
        },
    }
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    # Transport HTTP factice pour KrakenClient
    monkeypatch.setenv("DIA_HTTP_TRANSPORT", "dummy")
    monkeypatch.setenv("KRAKEN_API_KEY", "key")
    monkeypatch.setenv("KRAKEN_API_SECRET", "c2VjcmV0")  # "secret" en base64

    # Monkeypatch du constructeur KrakenClient pour injecter le transport
    import dia_core.kraken.client as kmod

    orig_init = kmod.KrakenClient.__init__

    def _init(self: kmod.KrakenClient, cfg: kmod.KrakenClientConfig) -> None:
        cfg2 = dataclasses.replace(cfg, transport=_DummyTransport())
        orig_init(self, cfg2)

    monkeypatch.setattr(kmod.KrakenClient, "__init__", _init)

    code = main(["--config", str(cfg_path)])  # main accepte argv et renvoie int
    assert code == 0
