from __future__ import annotations

import gzip
import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# --- registre pour éviter la double config ---
_CONFIGURED_LOGGERS: set[str] = set()


class _TradeIdFilter(logging.Filter):
    def __init__(self, trade_id: str | None) -> None:
        super().__init__()
        self._trade_id = trade_id

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trade_id"):
            record.trade_id = self._trade_id
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
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
    with open(source, "rb") as sf, gzip.open(dest, "wb", compresslevel=6) as df:
        df.write(sf.read())
    Path(source).unlink(missing_ok=True)


def _gz_namer(name: str) -> str:
    return f"{name}.gz"


def setup_logging(
    log_dir: str,
    level: str | int = "INFO",
    trade_id: str | None = None,
    filename: str = "app.log",
) -> logging.Logger:
    """
    Configure 'dia_core' en JSON, rotation gzip, filtre trade_id.
    Idempotent: ne reconfigure pas si déjà fait.
    """
    logger_name = "dia_core"
    logger = logging.getLogger(logger_name)

    if logger_name in _CONFIGURED_LOGGERS:
        return logger

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

    _CONFIGURED_LOGGERS.add(logger_name)
    return logger
