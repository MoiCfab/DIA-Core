# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : tests/test_journal_sqlite.py

Description :
Test unitaire de la persistance des ordres dans la base SQLite
via le module portfolio/journal.py. Vérifie que l'insertion d'un ordre
puis sa recuperation fonctionnent correctement.

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

from pathlib import Path

from dia_core.portfolio import journal


def test_journal_insert_order(tmp_path: Path) -> None:
    """Teste l'insertion et la lecture d'un ordre dans la base SQLite.

    Etapes :
        1. Cree une base SQLite temporaire.
        2. Insère un ordre fictif via journal.insert_order().
        3. Récupère l'ordre en base et vérifie les champs clefs.

    Args :
        tmp_path : Repertoire temporaire fourni par pytest pour isoler le test.
    """
    db = tmp_path / "orders.db"
    conn = journal.open_db(str(db))

    row = {
        "id": "TEST-1",
        "ts": 1234567890.0,
        "symbol": "BTC/EUR",
        "side": "buy",
        "type": "market",
        "qty": 0.01,
        "price": 20000.0,
        "status": "accepted",
        "reason": None,
    }
    journal.insert_order(conn, row)
    cur = conn.execute("SELECT id, symbol, side, status FROM orders WHERE id=?", ("TEST-1",))
    got = cur.fetchone()
    assert got == ("TEST-1", "BTC/EUR", "buy", "accepted")
