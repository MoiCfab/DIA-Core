from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Literal
from urllib.parse import urlencode

import httpx

from .errors import AuthError, ConnectivityError, OrderRejectedError, RateLimitError

logger = logging.getLogger("dia_core.kraken")

HTTP_TOO_MANY_REQUESTS = 429
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_SERVER_MIN = 500
HTTP_SERVER_MAX = 600  # exclusif


def _sign(path: str, data: dict[str, Any], secret: str) -> str:
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


@dataclass(frozen=True)
class RequestOpts:
    params: dict[str, Any] | None = None
    data: dict[str, Any] | None = None
    private: bool = False
    max_attempts: int = 3


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

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> KrakenClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        self.close()
        return False

    def _handle_response(self, resp: httpx.Response) -> dict[str, Any]:
        sc = resp.status_code
        if sc == HTTP_TOO_MANY_REQUESTS:
            raise RateLimitError("Rate limit (429)")
        if sc in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
            raise AuthError(f"Auth error ({sc})")
        if HTTP_SERVER_MIN <= sc < HTTP_SERVER_MAX:
            raise ConnectivityError(f"Server error {sc}")
        payload = resp.json()
        if isinstance(payload, dict) and payload.get("error"):
            raise OrderRejectedError(str(payload["error"]))
        return payload if isinstance(payload, dict) else {"result": payload}

    # ---------- Core request (args groupés) ----------
    def _request(self, method: str, path: str, *, opts: RequestOpts) -> dict[str, Any]:
        url = path
        headers: dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        body: bytes | None = None

        if opts.private:
            if not self.key or not self.secret:
                raise AuthError("Kraken API key/secret not configured")
            data = dict(opts.data or {})
            data.setdefault("nonce", int(time.time() * 1000))
            headers["API-Key"] = self.key  # type: ignore[assignment]
            headers["API-Sign"] = _sign(path, data, self.secret)  # type: ignore[arg-type]
            body = urlencode(data, doseq=True).encode()

        backoff = 0.5
        last_exc: Exception | None = None
        for attempt in range(1, opts.max_attempts + 1):
            try:
                resp = self._client.request(
                    method, url, params=opts.params, content=body, headers=headers
                )
                return self._handle_response(resp)
            except (httpx.HTTPError, ConnectivityError) as exc:
                last_exc = exc
                if attempt >= opts.max_attempts:
                    break
                time.sleep(backoff)
                backoff *= 2.0

        if last_exc is None:
            raise ConnectivityError("Network failure after retries (unknown error)")
        raise ConnectivityError(f"Network failure after retries: {last_exc!r}")

    # ---------- Endpoints utiles ----------
    def get_ohlc(self, pair: str, interval: int = 1) -> dict[str, Any]:
        params = {"pair": pair, "interval": interval}
        return self._request("GET", "/0/public/OHLC", opts=RequestOpts(params=params))

    def add_order(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.dry_run:
            fake_tx = f"DIA-DRYRUN-{int(time.time() * 1000)}"
            logger.info("Dry-run AddOrder", extra={"extra": {"txid": fake_tx}})
            return {"result": {"txid": [fake_tx]}}
        return self._request(
            "POST", "/0/private/AddOrder", opts=RequestOpts(data=data, private=True)
        )
