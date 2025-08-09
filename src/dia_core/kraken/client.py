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


def _sign(path: str, data: Dict[str, Any], secret: str) -> str:
    """
    Kraken signature: base64(hmac_sha512(sha256(nonce+postdata) + path, secret))
    """
    postdata = urlencode(data or {}, doseq=True)
    sha = hashlib.sha256((str(data.get("nonce", "")) + postdata).encode()).digest()
    msg = path.encode() + sha
    mac = hmac.new(base64.b64decode(secret), msg, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


# NEW: regroupe les paramètres pour éviter PLR0913
@dataclass(frozen=True)
class KrakenClientConfig:
    base_url: str = "https://api.kraken.com"
    key: str | None = None
    secret: str | None = None
    dry_run: bool = True
    timeout_s: float = 10.0
    transport: httpx.BaseTransport | None = None  # pour tests


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

    @classmethod
    def from_args(
        cls,
        base_url: str = "https://api.kraken.com",
        *,
        key: str | None = None,
        secret: str | None = None,
        dry_run: bool = True,
        timeout_s: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> "KrakenClient":
        """
        Compat pratique pour ne pas toucher tous les appelants tout de suite.
        """
        return cls(
            KrakenClientConfig(
                base_url=base_url,
                key=key,
                secret=secret,
                dry_run=dry_run,
                timeout_s=timeout_s,
                transport=transport,
            )
        )

    def close(self) -> None:
        self._client.close()

    # ---------- Core request avec retries ----------
    def _request(
        self,
        method: str,
        path: str,
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
            headers["API-Key"] = self.key
            headers["API-Sign"] = _sign(path, data, self.secret)  # type: ignore[arg-type]
            body = urlencode(data, doseq=True).encode()

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
    def get_ohlc(self, pair: str, interval: int = 1) -> Dict[str, Any]:
        params = {"pair": pair, "interval": interval}
        return self._request("GET", "/0/public/OHLC", params=params, private=False)

    def add_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.dry_run:
            fake_tx = f"DIA-DRYRUN-{int(time.time()*1000)}"
            logger.info("Dry-run AddOrder", extra={"extra": {"txid": fake_tx}})
            return {"result": {"txid": [fake_tx]}}
        return self._request("POST", "/0/private/AddOrder", data=data, private=True)
