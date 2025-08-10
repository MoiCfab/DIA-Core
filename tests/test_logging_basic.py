# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : tests/test_logging_basic.py

Description :
Test unitaire du module logging/setup.py.
Vérifie que la configuration du logger produit bien un fichier de log
au format JSON, contenant les champs attendus.

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import json
import logging
import os
from glob import glob
from pathlib import Path

from dia_core.logging import setup_logging


def test_logging_json_line(tmp_path: Path) -> None:
    """Teste que le logger écrit une ligne JSON correcte dans un fichier .log.

    Étapes :
        1. Configure un logger avec setup_logging().
        2. Écrit un message avec un champ "extra".
        3. Flush les handlers pour forcer l'écriture disque.
        4. Lit le fichier log et vérifie :
            qu'il existe et n'est pas vide,
            que la ligne est bien un JSON valide,
            que les champs level, trade_id, msg et extra sont corrects.

    Args :
        tmp_path : Repertoire temporaire fourni par pytest.
    """
    log_dir = tmp_path.as_posix()
    logger = setup_logging(log_dir, level="INFO", trade_id="smoketest", filename="unit.log")

    # Ecrit une entree
    logging.getLogger("dia_core.test").info("hello world", extra={"extra": {"k": "v"}})

    # Flush des handlers pour garantir l'ecriture disque
    for h in logger.handlers:
        h.flush()

    files = sorted(glob(os.path.join(log_dir, "*.log")))
    assert files, "Aucun fichier .log cree"

    body = Path(files[0]).read_text(encoding="utf-8").strip()
    assert body, "Fichier de log vide"

    # Chaque ligne est un JSON (unitaire: une ligne)
    payload = json.loads(body)
    assert payload["level"] == "INFO"
    assert payload["trade_id"] == "smoketest"
    assert payload["msg"] == "hello world"
    assert payload.get("extra", {}).get("k") == "v"
