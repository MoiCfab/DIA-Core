from __future__ import annotations
import os
import time
import hmac
import hashlib
import base64
import logging
from typing import Any, Dict, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .errors import KrakenNetworkError, KrakenRateLimit, KrakenAuthError

logger = logging.getLogger(__name__)
KRAKEN_API_URL = "https://api.kraken.com"


def _nonce() -> str:
    return str(int(time.time() * 1000))


def _sign(path: str, data: Dict[str, Any], secret: str) -> str:
    postdata = httpx.QueryParams(data).encode()
    encoded = str(data.get("nonce")).encode() + postdata
    message = path.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


class KrakenClient:
    def __init__(
        self, key: Optional[str] = None, secret: Optional[str] = None, timeout: float = 10.0
    ):
        self.key = key or os.getenv("KRAKEN_API_KEY", "")
        self.secret = secret or os.getenv("KRAKEN_API_SECRET", "")
        self.timeout = timeout
        self._client = httpx.Client(timeout=self.timeout)
        if not self.key or not self.secret:
            logger.warning(
                "Kraken API keys not set; private endpoints will fail.",
                extra={"component": "kraken"},
            )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((KrakenNetworkError, KrakenRateLimit)),
    )
    def _request(
        self, method: str, path: str, data: Optional[Dict[str, Any]] = None, private: bool = False
    ) -> Dict[str, Any]:
        url = f"{KRAKEN_API_URL}{path}"
        headers = {}
        data = data or {}

        if private:
            data["nonce"] = _nonce()
            headers["API-Key"] = self.key
            headers["API-Sign"] = _sign(path, data, self.secret)

        try:
            if method == "POST":
                r = self._client.post(url, data=data, headers=headers)
            else:
                r = self._client.get(url, params=data, headers=headers)
        except httpx.RequestError as e:
            logger.warning(
                "Network error to Kraken", extra={"component": "kraken", "reason": str(e)}
            )
            raise KrakenNetworkError(str(e)) from e

        if r.status_code == 429:
            raise KrakenRateLimit("Rate limited by Kraken")
        if r.status_code in (401, 403):
            raise KrakenAuthError("Auth failed")
        if r.status_code >= 500:
            raise KrakenNetworkError(f"Server error {r.status_code}")

        payload = r.json()
        if payload.get("error"):
            raise KrakenNetworkError(str(payload["error"]))

        return payload.get("result", payload)

    # Exemple public : OHLC
    def get_ohlc(self, pair: str, interval: int = 5, since: Optional[int] = None) -> Dict[str, Any]:
        params = {"pair": pair, "interval": interval}
        if since:
            params["since"] = since
        return self._request("GET", "/0/public/OHLC", params, private=False)

    # Exemple privé : création d'ordre
    def add_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/0/private/AddOrder", data, private=True)
