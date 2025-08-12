# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : logging/setup.py

Description :
Fournit la configuration de logging structuree pour DIA-Core.
Les logs sont enregistrés en JSON, avec rotation et compression gzip.
Chaque entree peut contenir un identifiant de trade pour faciliter le suivi.
Le systeme est base sur `logging` standard de Python, avec un formatter
et un filtre personnalises.

Utilise par :
    main.py (initialisation logging au demarrage)
    tous les modules dia_core (journalisation structuree)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
import gzip
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# --- Registre pour eviter la double configuration des loggers ---
_CONFIGURED_LOGGERS: set[str] = set()


class _TradeIdFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    """Filtre qui ajoute un identifiant de trade a chaque entree de log."""

    def __init__(self, trade_id: str | None) -> None:
        super().__init__()
        self._trade_id = trade_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Ajoute le champ trade_id au record s'il n'existe pas deja.

        Args:
          record: logging.LogRecord:

        Returns:

        """
        if not hasattr(record, "trade_id"):
            record.trade_id = self._trade_id
        return True


class _JsonFormatter(logging.Formatter):
    """Formatter qui convertit chaque log en entree JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Formate un log record en JSON avec timestamp, niveau, nom et message.

        Args:
          record: logging.LogRecord:

        Returns:

        """
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
            "trade_id": getattr(record, "trade_id", None),
        }
        extra_val = getattr(record, "extra", None)
        if isinstance(extra_val, dict):
            payload["extra"] = extra_val
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _gzip_rotator(source: str, dest: str) -> None:
    """Fonction de rotation pour compresser un fichier log en .gz.

    Args:
      source: str:
      dest: str:

    Returns:

    """
    with open(source, "rb") as sf, gzip.open(dest, "wb", compresslevel=6) as df:
        df.write(sf.read())
    Path(source).unlink(missing_ok=True)


def _gz_namer(name: str) -> str:
    """Ajoute l'extension .gz au nom du fichier de log.

    Args:
      name: str:

    Returns:

    """
    return f"{name}.gz"


def setup_logging(
    log_dir: str,
    level: str | int = "INFO",
    trade_id: str | None = None,
    filename: str = "app.log",
) -> logging.Logger:
    """Configure le logger principal de DIA-Core avec sortie JSON et rotation gzip.

    Args:
      log_dir: Repertoire ou stocker les fichiers de log.
      level: Niveau de log ("INFO", "DEBUG", int, etc.).
      trade_id: Identifiant optionnel de trade a inclure dans tous les logs.
      filename: Nom du fichier log principal.
      log_dir: str:
      level: str | int:  (Default value = "INFO")
      trade_id: str | None:  (Default value = None)
      filename: str:  (Default value = "app.log")

    Returns:
      : Logger configure et pret a l'emploi.

    """
    logger = logging.getLogger("dia_core")

    # Nettoie les handlers precedents
    for h in list(logger.handlers):
        logger.removeHandler(h)
        with contextlib.suppress(Exception):
            h.close()

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logfile = Path(log_dir) / filename
    logfile.touch(exist_ok=True)

    handler = RotatingFileHandler(
        filename=str(logfile),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.rotator = _gzip_rotator
    handler.namer = _gz_namer
    handler.setFormatter(_JsonFormatter())
    handler.addFilter(_TradeIdFilter(trade_id))

    lvl_num = level if isinstance(level, int) else getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(lvl_num)
    logger.addHandler(handler)
    logger.propagate = False

    # S'assure que les sous-loggers propagent bien vers "dia_core"
    logging.getLogger("dia_core.test").propagate = True

    return logger
