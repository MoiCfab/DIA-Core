# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : tests/test_kraken_client.py

Description :
Tests unitaires pour le client Kraken (kraken/client.py).
Vérifie le bon comportement de l'appel d'API OHLC, la gestion
des retries en cas d'erreur serveur, le traitement des erreurs
de type rate limit et auth, ainsi que le mode dry_run pour add_order.

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from dia_core.kraken.client import KrakenClient, KrakenClientConfig
from dia_core.kraken.errors import AuthError, RateLimitError


def _transport_with_sequence(responses: list[httpx.Response]) -> httpx.MockTransport:
    """Cree un MockTransport HTTP renvoyant une sequence de réponses prédéfinies.

    Args:
        responses: Liste de réponses HTTP a renvoyer dans l'ordre.

    Returns:
        Un objet httpx.MockTransport simulant ces reponses.
    """
    it = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        try:
            return next(it)
        except StopIteration:
            # Si plus de reponses prevues, renvoyer 500 pour forcer l'echec
            return httpx.Response(500, request=request)

    return httpx.MockTransport(handler)


def test_get_ohlc_success() -> None:
    """Teste que get_ohlc renvoie correctement les donnees OHLC du payload."""
    payload: dict[str, Any] = {"error": [], "result": {"XXBTZEUR": [[1, 2, 3]]}}
    transport = _transport_with_sequence([httpx.Response(200, json=payload)])
    client = KrakenClient(KrakenClientConfig(dry_run=True, transport=transport))
    out = client.get_ohlc("XXBTZEUR", 1)
    assert out["result"]["XXBTZEUR"][0][0] == 1
    client.close()


def test_retry_on_5xx() -> None:
    """Teste que le client retente la requête apres une erreur serveur 5xx."""
    ok_payload: dict[str, Any] = {"error": [], "result": {"XXBTZEUR": [[1]]}}
    transport = _transport_with_sequence(
        [
            httpx.Response(502),  # 1er essai -> 5xx
            httpx.Response(200, json=ok_payload),  # 2e essai -> OK
        ]
    )
    client = KrakenClient(KrakenClientConfig(dry_run=True, transport=transport))
    out = client.get_ohlc("XXBTZEUR", 1)
    assert out["result"]["XXBTZEUR"][0][0] == 1
    client.close()


def test_rate_limit_raises() -> None:
    """Teste que le client leve RateLimitError en cas de HTTP 429."""
    transport = _transport_with_sequence([httpx.Response(429)])
    client = KrakenClient(KrakenClientConfig(dry_run=True, transport=transport))
    with pytest.raises(RateLimitError):
        client.get_ohlc("XXBTZEUR", 1)
    client.close()


def test_auth_error_raises() -> None:
    """Teste que le client leve AuthError en cas de HTTP 401/403."""
    transport = _transport_with_sequence([httpx.Response(401)])
    client = KrakenClient(KrakenClientConfig(dry_run=True, transport=transport))
    with pytest.raises(AuthError):
        client.get_ohlc("XXBTZEUR", 1)
    client.close()


def test_add_order_dry_run() -> None:
    """Teste que add_order ne fait aucun appel réseau en mode dry_run."""
    called = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["n"] += 1
        return httpx.Response(200, json={"error": [], "result": {"txid": ["should-not-be-used"]}})

    transport = httpx.MockTransport(handler)
    client = KrakenClient(KrakenClientConfig(dry_run=True, transport=transport))
    out = client.add_order({"pair": "XXBTZEUR", "type": "buy"})
    assert "txid" in out["result"]
    assert called["n"] == 0, "En dry_run, aucun appel reseau ne doit partir"
    client.close()
