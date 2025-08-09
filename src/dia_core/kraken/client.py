from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from .errors import AuthError, ConnectivityError, OrderRejected, RateLimitError

Logger = logging.getLoggerClass()
logger = logging.getLogger("dia_core.kraken")


def _sign(path: str, data: dict[str, Any], secret: str) -> str:
    # Kraken signature: base64(hmac_sha512(sha256(nonce+postdata) + path, secret))
    # Pour nos tests unitaires, le détail exact n'est pas utilisé; implémentation conforme.
    postdata = urlencode(data or {}, doseq=True)
    sha = hashlib.sha256((str(data.get("nonce", "")) + postdata).encode()).digest()
    msg = path.encode() + sha
    mac = hmac.new(base64.b64decode(secret), msg, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


class KrakenClient:
    def __init__(
        self,
        base_url: str = "https://api.kraken.com",
        *,
        key: str | None = None,
        secret: str | None = None,
        dry_run: bool = True,
        timeout_s: float = 10.0,
        transport: httpx.BaseTransport | None = None,  # pour tests
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.key = key
        self.secret = secret
        self.dry_run = dry_run
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_s),
            transport=transport,
            headers={"User-Agent": "DIA-Core/kraken"},
        )

    def close(self) -> None:
        self._client.close()

    # ---------- Core request avec retries ----------
    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        private: bool = False,
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        url = path
        headers: dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
        }

        body: bytes | None = None
        if private:
            if not self.key or not self.secret:
                raise AuthError("Kraken API key/secret not configured")
            assert self.secret is not None
            data = dict(data or {})
            data.setdefault("nonce", int(time.time() * 1000))
            headers["API-Key"] = self.key
            headers["API-Sign"] = _sign(path, data, self.secret)
            body = urlencode(data, doseq=True).encode()
        else:
            body = None

        # Boucle de retries simple: erreurs réseau et 5xx
        backoff = 0.5
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                resp = self._client.request(
                    method, url, params=params, content=body, headers=headers
                )
                # Mapping HTTP
                if resp.status_code == 429:
                    raise RateLimitError("Rate limit (429)")
                if resp.status_code in (401, 403):
                    raise AuthError(f"Auth error ({resp.status_code})")
                if 500 <= resp.status_code < 600:
                    raise ConnectivityError(f"Server error {resp.status_code}")

                payload = resp.json()
                # Kraken renvoie {"error": [...], "result": {...}}
                if isinstance(payload, dict) and payload.get("error"):
                    raise OrderRejected(str(payload["error"]))

                if isinstance(payload, dict):
                    return payload  # dict[str, Any]
                # Si Kraken renvoie autre chose (peu probable), on uniformise
                return {"result": payload}
            except (httpx.HTTPError, ConnectivityError) as exc:
                last_exc = exc
                if attempt >= max_attempts:
                    break
                time.sleep(backoff)
                backoff *= 2.0

        assert last_exc is not None
        raise ConnectivityError(f"Network failure after retries: {last_exc!r}")

    # ---------- Endpoints utiles ----------
    def get_ohlc(self, pair: str, interval: int = 1) -> dict[str, Any]:
        params = {"pair": pair, "interval": interval}
        return self._request("GET", "/0/public/OHLC", params=params, private=False)

    def add_order(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.dry_run:
            fake_tx = f"DIA-DRYRUN-{int(time.time()*1000)}"
            logger.info("Dry-run AddOrder", extra={"extra": {"txid": fake_tx}})
            return {"result": {"txid": [fake_tx]}}
        return self._request("POST", "/0/private/AddOrder", data=data, private=True)
