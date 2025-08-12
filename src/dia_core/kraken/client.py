# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : kraken/client.py

Description :
Client HTTP pour l'API Kraken, avec signature des requetes privees, gestion
des erreurs, retries avec backoff exponentiel, et mode dry-run.
Expose des methodes utilitaires pour:
- recuperer des OHLC publiques,
- soumettre un ordre (AddOrder) avec validation serveur.

Utilise par :
    data/provider.py (telechargement OHLC)
    exec/executor.py (soumission et validation d'ordre)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import logging
import time
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
    """Calcule la signature Kraken pour une requete privee.

    La signature utilise:
      mac = HMAC_SHA512(secret_decoded, path + SHA256(nonce + postdata))

    Args:
      path: Chemin de l'endpoint (ex: "/0/private/AddOrder").
      data: Donnees du corps POST (incluant "nonce").
      secret: Cle API privee en Base64.
      path: str:
      data: dict[str:
      Any]:
      secret: str:

    Returns:
      : Chaine Base64 representant la signature a placer dans l'entete "API-Sign".

    """
    postdata = urlencode(data or {}, doseq=True)
    sha = hashlib.sha256((str(data.get("nonce", "")) + postdata).encode()).digest()
    msg = path.encode() + sha
    mac = hmac.new(base64.b64decode(secret), msg, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


@dataclass(frozen=True)
class KrakenClientConfig:
    """Configuration du client Kraken."""

    base_url: str = "https://api.kraken.com"
    key: str | None = None
    secret: str | None = None
    dry_run: bool = True
    timeout_s: float = 10.0
    transport: httpx.BaseTransport | None = None  # tests


@dataclass(frozen=True)
class RequestOpts:
    """Options de requete internes."""

    params: dict[str, Any] | None = None
    data: dict[str, Any] | None = None
    private: bool = False
    max_attempts: int = 3


class KrakenClient:
    """Client synchrone pour l'API Kraken base sur httpx.Client.

    Ce client gere:
      - la signature des endpoints prives,
      - la normalisation des reponses JSON,
      - la detection des erreurs HTTP et "payload['error']",
      - un retry simple avec backoff exponentiel sur erreurs reseau/serveur.

    Args:

    Returns:

    """

    def __init__(self, cfg: KrakenClientConfig) -> None:
        """Construit le client httpx avec configuration et headers par defaut."""
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
        """Ferme le client HTTP sous-jacent."""
        self._client.close()

    def __enter__(self) -> KrakenClient:
        """Support du context manager (with KrakenClient(...) as c: ...)."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        """Ferme automatiquement le client a la sortie du contexte."""
        self.close()
        return False

    def _handle_response(self, resp: httpx.Response) -> dict[str, Any]:
        """Traduit la reponse HTTP en payload Python et leve en cas d'erreur.

        Args:
          resp: Reponse httpx.
          resp: httpx.Response:

        Returns:
          : Un dictionnaire representant le payload normalise.

        Raises:
          RateLimitError: 429.
          AuthError: 401 ou 403.
          ConnectivityError: erreurs serveur 5xx.
          OrderRejectedError: si "error" est renseigne dans la reponse Kraken.

        """
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

    def _request(self, method: str, path: str, *, opts: RequestOpts) -> dict[str, Any]:
        """Effectue une requete HTTP signe si necessaire, avec retries.

        Args:
          method: "GET" ou "POST".
          path: Chemin d'endpoint Kraken (ex: "/0/public/OHLC").
          opts: Options de requete (params, data, private, max_attempts).
          method: str:
          path: str:
          *:
          opts: RequestOpts:

        Returns:
          : Payload JSON sous forme de dict.

        Raises:
          AuthError: si une requete privee est appelee sans cles.
          ConnectivityError: en cas d'echec apres retries.
          RateLimitError, OrderRejectedError: propagees depuis _handle_response.

        """
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
            headers["API-Key"] = self.key
            headers["API-Sign"] = _sign(path, data, self.secret)
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
        """Recupere des bougies OHLC publiques.

        Args:
          pair: Symbole de la paire (ex: "XXBTZEUR").
          interval: Intervalle en minutes.
          pair: str:
          interval: int:  (Default value = 1)

        Returns:
          : Payload JSON normalise de l'endpoint OHLC.

        """
        params = {"pair": pair, "interval": interval}
        return self._request("GET", "/0/public/OHLC", opts=RequestOpts(params=params))

    def add_order(self, data: dict[str, Any]) -> dict[str, Any]:
        """Soumet un ordre AddOrder cote Kraken.

        En mode dry_run, retourne un faux txid et ne contacte pas Kraken.
        Sinon, envoie un POST prive avec signature.

        Args:
          data: Corps POST attendu par Kraken AddOrder.
          data: dict[str:
          Any]:

        Returns:
          : Payload JSON normalise de l'endpoint AddOrder ou reponse simulee.

        Raises:
          AuthError, RateLimitError, OrderRejectedError, ConnectivityError:
            selon les erreurs detectees par _request et _handle_response.

        """
        if self.dry_run:
            fake_tx = f"DIA-DRYRUN-{int(time.time() * 1000)}"
            logger.info("Dry-run AddOrder", extra={"extra": {"txid": fake_tx}})
            return {"result": {"txid": [fake_tx]}}
        return self._request(
            "POST", "/0/private/AddOrder", opts=RequestOpts(data=data, private=True)
        )
