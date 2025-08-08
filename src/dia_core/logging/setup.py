from __future__ import annotations

import gzip
import io
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timezone


class _TradeIdFilter(logging.Filter):
    """Injecte un trade_id dans chaque record (si fourni)."""

    def __init__(self, trade_id: Optional[str]) -> None:
        super().__init__()
        self._trade_id = trade_id

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        # Ajoute l'attribut si absent
        if not hasattr(record, "trade_id"):
            record.trade_id = self._trade_id  # type: ignore[attr-defined]
        return True


class _JsonFormatter(logging.Formatter):
    """Formatter JSON minimal et stable."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
            "trade_id": getattr(record, "trade_id", None),
        }
        # On accepte un champ "extra" dict passé via extra={"extra": {...}}
        extra_val = getattr(record, "extra", None)
        if isinstance(extra_val, dict):
            payload["extra"] = extra_val
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _gzip_rotator(source: str, dest: str) -> None:
    """Compresse le fichier de rotation en .gz."""
    with open(source, "rb") as sf, gzip.open(dest, "wb", compresslevel=6) as df:
        df.write(sf.read())
    Path(source).unlink(missing_ok=True)


def _gz_namer(name: str) -> str:
    return f"{name}.gz"


def setup_logging(
    log_dir: str,
    level: str = "INFO",
    trade_id: Optional[str] = None,
    filename: str = "app.log",
) -> logging.Logger:
    """
    Configure un logger 'dia_core' avec:
    - format JSON
    - rotation gzip (max 5MB, 5 backups)
    - filtre trade_id
    - pas de double config si déjà fait
    """
    logger = logging.getLogger("dia_core")
    # Évite reconfiguration
    if getattr(logger, "_configured", False):  # type: ignore[attr-defined]
        return logger

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logfile = Path(log_dir) / filename

    handler = RotatingFileHandler(
        filename=str(logfile),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    # Rotation compressée
    handler.rotator = _gzip_rotator  # type: ignore[assignment]
    handler.namer = _gz_namer  # type: ignore[assignment]

    handler.setFormatter(_JsonFormatter())
    handler.addFilter(_TradeIdFilter(trade_id))

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.addHandler(handler)
    logger.propagate = False  # évite les doublons vers le root

    # Flag interne pour éviter reconfiguration
    setattr(logger, "_configured", True)
    return logger
