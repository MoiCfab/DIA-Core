from __future__ import annotations

import json
from typing import Any, Dict

import httpx
import pytest

from dia_core.kraken.client import KrakenClient
from dia_core.kraken.errors import AuthError, ConnectivityError, RateLimitError


def _transport_with_sequence(responses: list[httpx.Response]) -> httpx.MockTransport:
    it = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        try:
            return next(it)
        except StopIteration:
            # Si plus de réponses prévues, renvoyer 500 pour forcer l'échec
            return httpx.Response(500, request=request)

    return httpx.MockTransport(handler)


def test_get_ohlc_success() -> None:
    payload: Dict[str, Any] = {"error": [], "result": {"XXBTZEUR": [[1, 2, 3]]}}
    transport = _transport_with_sequence(
        [httpx.Response(200, json=payload)]
    )
    client = KrakenClient(dry_run=True, transport=transport)
    out = client.get_ohlc("XXBTZEUR", 1)
    assert out["result"]["XXBTZEUR"][0][0] == 1
    client.close()


def test_retry_on_5xx() -> None:
    ok_payload: Dict[str, Any] = {"error": [], "result": {"XXBTZEUR": [[1]]}}
    transport = _transport_with_sequence(
        [
            httpx.Response(502),               # 1er essai -> 5xx
            httpx.Response(200, json=ok_payload),  # 2e essai -> OK
        ]
    )
    client = KrakenClient(dry_run=True, transport=transport)
    out = client.get_ohlc("XXBTZEUR", 1)
    assert out["result"]["XXBTZEUR"][0][0] == 1
    client.close()


def test_rate_limit_raises() -> None:
    transport = _transport_with_sequence([httpx.Response(429)])
    client = KrakenClient(dry_run=True, transport=transport)
    with pytest.raises(RateLimitError):
        client.get_ohlc("XXBTZEUR", 1)
    client.close()


def test_auth_error_raises() -> None:
    transport = _transport_with_sequence([httpx.Response(401)])
    client = KrakenClient(dry_run=True, transport=transport)
    with pytest.raises(AuthError):
        client.get_ohlc("XXBTZEUR", 1)
    client.close()


def test_add_order_dry_run() -> None:
    called = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        called["n"] += 1
        return httpx.Response(200, json={"error": [], "result": {"txid": ["should-not-be-used"]}})

    transport = httpx.MockTransport(handler)
    client = KrakenClient(dry_run=True, transport=transport)
    out = client.add_order({"pair": "XXBTZEUR", "type": "buy"})
    assert "txid" in out["result"]
    assert called["n"] == 0, "En dry-run, aucun appel réseau ne doit partir"
    client.close()
