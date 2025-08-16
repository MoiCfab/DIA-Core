# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : alerts/telegram_alerts.py

Description :
Gère l'envoi de messages via Telegram grâce à un bot.
Lit la configuration depuis les variables d`environnement ou
peut être appelée directement avec un token + chat_id.

Utilisé par :
    TradeNotifier
    Modules d`alerte système (drawdown, crash…)

Auteur : DYXIUM Invest / D.I.A. Core
"""

import os
import requests
from dataclasses import dataclass

HTTP_OK = 200


@dataclass
class TgConfig:
    """Structure de configuration Telegram."""

    token: str
    chat_id: str


def load_config_from_env() -> TgConfig | None:
    """
    Charge la config Telegram depuis les variables d`environnement.

    Returns :
        TgConfig ou None si clé manquante
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return None
    return TgConfig(token=token, chat_id=chat_id)


def send(config: TgConfig | None, message: str) -> bool:
    """
    Envoie un message Telegram via bot API.

    Args:
        config: TgConfig ou None
        message: str

    Returns:
        bool: True si succès, False sinon
    """
    if config is None:
        return False

    url = f"https://api.telegram.org/bot{config.token}/sendMessage"
    payload = {"chat_id": config.chat_id, "text": message, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == HTTP_OK
    except requests.RequestException as e:
        print(f"[Telegram] Erreur : {e}")
        return False
