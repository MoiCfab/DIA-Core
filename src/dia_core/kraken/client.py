from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import urlencode

import httpx

from .errors import AuthError, ConnectivityError, OrderRejected, RateLimitError

logger = logging.getLogger("dia_core.kraken")

# --- Constantes HTTP (évite magic numbers) ---
HTTP_TOO_MANY_REQUESTS = 429
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_SERVER_MIN = 500
HTTP_SERVER_MAX = 600  # exclusif


def _sign(path: str, data: Dict[str, Any], secret: str) -> str:
    """Kraken: base64(hmac_sha512(sha256(nonce+postdata) + path, secret))."""
    postdata = urlencode(data or {}, doseq=True)
    sha = hashlib.sha256((str(data.get("nonce", "")) + postdata).encode()).digest()
    msg = path.encode() + sha
    mac = hmac.new(base64.b64decode(secret), msg, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()

@dataclass(frozen=True)
class KrakenClientConfig:
    base_url: str = "https://api.kraken.com"
    key: str | None = None
    secret: str | None = None
    dry_run: bool = True
    timeout_s: float = 10.0
    transport: httpx.BaseTransport | None = None  # tests

class KrakenClient:
    def __init__(self, cfg: KrakenClientConfig) -> None:
        self.base_url = cfg.base_url.rstrip("/")
        self.key = cfg.key
        self.secret = cfg.secret
        self.dry_run = cfg.dry_run
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(cfg.timeout_s),
            transport=cfg.transport,
            headers={"User-Agent": "DIA-Core/kraken"},
        )

    # ---------- Core request (args groupés) ----------
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Dict[str, Any] | None = None,
        data: Dict[str, Any] | None = None,
        private: bool = False,
        max_attempts: int = 3,
    ) -> Dict[str, Any]:
        url = path
        headers: Dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
        }

        body: bytes | None = None
        if private:
            if not self.key or not self.secret:
                raise AuthError("Kraken API key/secret not configured")
            data = dict(data or {})
            data.setdefault("nonce", int(time.time() * 1000))
            headers["API-Key"] = self.key  # type: ignore[assignment]
            headers["API-Sign"] = _sign(path, data, self.secret)  # type: ignore[arg-type]
            body = urlencode(data, doseq=True).encode()

        backoff = 0.5
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                resp = self._client.request(
                    method, url, params=params, content=body, headers=headers
                )
                sc = resp.status_code
                if sc == HTTP_TOO_MANY_REQUESTS:
                    raise RateLimitError("Rate limit (429)")
                if sc in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
                    raise AuthError(f"Auth error ({sc})")
                if HTTP_SERVER_MIN <= sc < HTTP_SERVER_MAX:
                    raise ConnectivityError(f"Server error {sc}")

                payload = resp.json()
                if isinstance(payload, dict) and payload.get("error"):
                    raise OrderRejected(str(payload["error"]))  # N818 ailleurs si tu renomme

                if isinstance(payload, dict):
                    return payload
                return {"result": payload}
            except (httpx.HTTPError, ConnectivityError) as exc:
                last_exc = exc
                if attempt >= max_attempts:
                    break
                time.sleep(backoff)
                backoff *= 2.0

        if last_exc is None:
            raise ConnectivityError("Network failure after retries (unknown error)")
        raise ConnectivityError(f"Network failure after retries: {last_exc!r}")

    # ---------- Endpoints utiles ----------
    def get_ohlc(self, pair: str, interval: int = 1) -> Dict[str, Any]:
        params = {"pair": pair, "interval": interval}
        return self._request("GET", "/0/public/OHLC", params=params, private=False)

    def add_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.dry_run:
            fake_tx = f"DIA-DRYRUN-{int(time.time() * 1000)}"
            logger.info("Dry-run AddOrder", extra={"extra": {"txid": fake_tx}})
            return {"result": {"txid": [fake_tx]}}
        return self._request("POST", "/0/private/AddOrder", data=data, private=True)
