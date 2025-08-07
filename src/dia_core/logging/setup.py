from __future__ import annotations
import logging, os, json, gzip, shutil
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
        }
        for k in ("pair", "strategy", "order_id", "mode", "component"):
            if hasattr(record, k):
                payload[k] = getattr(record, k)
        return json.dumps(payload, ensure_ascii=False)

class GzipRotatingFileHandler(RotatingFileHandler):
    def doRollover(self) -> None:
        super().doRollover()
        for i in range(self.backupCount, 0, -1):
            fn = f"{self.baseFilename}.{i}"
            if os.path.exists(fn) and not fn.endswith(".gz"):
                with open(fn, "rb") as src, gzip.open(fn + ".gz", "wb") as dst:
                    shutil.copyfileobj(src, dst)
                os.remove(fn)

def setup_logging(log_dir: str, level: int = logging.INFO) -> None:
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "runtime.log")
    root = logging.getLogger()
    root.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(JsonLogFormatter())
    root.addHandler(ch)

    fh = GzipRotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=5)
    fh.setLevel(level)
    fh.setFormatter(JsonLogFormatter())
    root.addHandler(fh)
