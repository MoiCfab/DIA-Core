# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : alerts/telegram_alerts.py

Description :
    Envoi d'alertes Telegram optionnelles, en complément des emails.
    Par défaut, fonctionne en *dry_run* pour la CI et les tests.

    Variables d'env supportées :
        TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DIA_TELEGRAM_DRY_RUN

    Aucune dépendance externe (httpx) dans ce module pour éviter le réseau
    en test : on expose un *payload builder* et un *sender* basique qui peut
    être mocké/contourné au niveau application si nécessaire.

Auteur : DYXIUM Invest / D.I.A. Core
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

_API_URL_TMPL: Final[str] = "https://api.telegram.org/bot{token}/sendMessage"
_HTTP_OK_MIN: Final[int] = 200
_HTTP_OK_MAX_EXCL: Final[int] = 300


@dataclass(frozen=True)
class TgConfig:
    token: str
    chat_id: str
    dry_run: bool = True


def load_config_from_env() -> TgConfig | None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    dry = os.environ.get("DIA_TELEGRAM_DRY_RUN", "1") != "0"
    if not token or not chat:
        return None
    return TgConfig(token=token, chat_id=chat, dry_run=dry)


def build_payload(cfg: TgConfig, text: str) -> tuple[str, bytes]:
    url = _API_URL_TMPL.format(token=cfg.token)
    body = {"chat_id": cfg.chat_id, "text": text}
    return url, json.dumps(body).encode("utf-8")


def send(cfg: TgConfig, text: str, *, transport: Callable[[str, bytes], int] | None = None) -> bool:
    """Envoie un message. En dry_run, ne fait qu'assembler le payload.

    Args:
        cfg: configuration Telegram
        text: contenu
        transport: callable optionnel (url: str, body: bytes) -> int (status)
    """
    url, body = build_payload(cfg, text)
    if cfg.dry_run:
        return True
    if transport is None:
        raise RuntimeError("No transport provided in live mode")
    code = int(transport(url, body))
    return _HTTP_OK_MIN <= code < _HTTP_OK_MAX_EXCL
