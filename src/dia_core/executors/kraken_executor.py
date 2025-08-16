# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : exec/executors/kraken_executor.py

Description :
Exécuteur réel basé sur l'API privée de Kraken.
Permet d'envoyer des ordres de marché live (buy/sell).

Utilisé par :
    - BotEngine (via injection live)
    - ExecutionController (mode = live)

Auteur : DYXIUM Invest / D.I.A. Core
"""

import os
import time
import hashlib
import hmac
import base64
from typing import Any

import requests

from urllib.parse import urlencode
from src.dia_core.models.intent import OrderIntent


def sign(urlpath: str, data: dict[str, Any], secret: str) -> str:
    """
    Crée une signature HMAC-SHA512 pour sécuriser l'appel API.

    Args:
      urlpath: str: endpoint
      data: dict: paramètres POST
      secret: str: clé secrète

    Returns:
      str: Signature encodée
    """
    postdata = urlencode(data)
    encoded = (str(data["nonce"]) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()


class KrakenExecutor:
    """Exécuteur réel utilisant l'API privée de Kraken."""

    def __init__(self) -> None:
        """
        Initialise le client Kraken depuis les variables d'environnement :
            KRAKEN_API_KEY
            KRAKEN_API_SECRET
        """
        self.api_key = str(os.environ.get("KRAKEN_API_KEY"))
        self.api_secret = str(os.environ.get("KRAKEN_API_SECRET"))

        if not self.api_key or not self.api_secret:
            raise RuntimeError("Clés API Kraken manquantes (KRAKEN_API_KEY / SECRET)")

        self.url = "https://api.kraken.com"
        self.api_version = "0"
        self.session = requests.Session()

    def _private_request(self, method: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Envoie une requête privée signée à Kraken.

        Args:
          method: str: nom de l' endpoint (AddOrder, etc.)
          data: dict: paramètres POST

        Returns:
          dict: réponse JSON
        """
        urlpath = f"/{self.api_version}/private/{method}"
        url = self.url + urlpath

        data["nonce"] = int(1000 * time.time())
        headers = {
            "API-Key": self.api_key,
            "API-Sign": sign(urlpath, data, self.api_secret),
        }

        response = self.session.post(url, headers=headers, data=data)
        result = response.json()

        if result.get("error"):
            raise RuntimeError(f"[Kraken] Erreur API : {result['error']}")

        output: dict[str, Any] = result.get("result", {})
        return output

    def submit(self, intent: OrderIntent, symbol: str) -> None:
        """
        Exécute un ordre réel sur Kraken.

        Args:
          intent: OrderIntent:
            L'action à prendre (buy/sell/hold)
          symbol: str:
            Symbole à trader, ex: "BTC/EUR"

        Returns:
          None
        """
        if intent.action == "hold":
            print(f"[KrakenExecutor] HOLD → aucun ordre envoyé pour {symbol}")
            return

        kraken_pair = symbol.replace("/", "").upper()  # "BTC/EUR" → "XBTEUR"
        data = {
            "pair": kraken_pair,
            "type": intent.action,
            "ordertype": "market",
            "volume": str(intent.size),
        }

        print(f"[KrakenExecutor] {symbol} → {intent.action.upper()} x {intent.size}")
        result = self._private_request("AddOrder", data)
        print(f"[Kraken] Order envoyé ✅ ID = {result.get('txid')}")
