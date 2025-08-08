from __future__ import annotations

import json
import logging
import os
from glob import glob
from pathlib import Path

from dia_core.logging import setup_logging


def test_logging_json_line(tmp_path: Path) -> None:
    log_dir = tmp_path.as_posix()
    logger = setup_logging(log_dir, level="INFO", trade_id="smoketest", filename="unit.log")

    # Écrit une entrée
    logging.getLogger("dia_core.test").info("hello world", extra={"extra": {"k": "v"}})

    # Flush des handlers pour garantir l'écriture disque
    for h in logger.handlers:
        h.flush()

    files = sorted(glob(os.path.join(log_dir, "*.log")))
    assert files, "Aucun fichier .log créé"

    body = Path(files[0]).read_text(encoding="utf-8").strip()
    assert body, "Fichier de log vide"

    # Chaque ligne est un JSON (unitaire: une ligne)
    payload = json.loads(body)
    assert payload["level"] == "INFO"
    assert payload["trade_id"] == "smoketest"
    assert payload["msg"] == "hello world"
    assert payload.get("extra", {}).get("k") == "v"
