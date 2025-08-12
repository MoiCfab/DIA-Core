# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : portfolio/journal.py

Description :
Gestion du journal de trading de DIA-Core via une base SQLite.
Permet d'enregistrer :
- les ordres (orders),
- les executions (trades),
- les evenements generaux (events).

Utilise par :
    main.py (journalisation des ordres et evenements)
    exec/executor.py (enregistrement apres execution d'ordre)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Any

# Schéma SQLite initialise lors de la creation de la base
SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    ts INTEGER,
    symbol TEXT,
    side TEXT,
    type TEXT,
    qty REAL,
    price REAL,
    status TEXT,
    reason TEXT
);
CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    ts INTEGER,
    order_id TEXT,
    symbol TEXT,
    qty REAL,
    price REAL,
    pnl REAL
);
CREATE TABLE IF NOT EXISTS events (
    ts INTEGER,
    level TEXT,
    component TEXT,
    message TEXT
);
"""


def open_db(path: str) -> sqlite3.Connection:
    """Cree ou ouvre la base SQLite et initialise le schema si necessaire.

    Args:
      path: Chemin vers le fichier SQLite (.sqlite).
      path: str:

    Returns:
      : Instance sqlite3.Connection ouverte en mode autocommit.

    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None)
    conn.executescript(SCHEMA)
    return conn


def insert_order(conn: sqlite3.Connection, row: dict[str, Any]) -> None:
    """Insere ou remplace une entree dans la table orders.

    Args:
      conn: Connexion SQLite.
      row: Dictionnaire contenant :
    id, ts, symbol, side, type, qty, price, status, reason.
    Les champs 'status' et 'reason' sont optionnels.
      conn: sqlite3.Connection:
      row: dict[str:
      Any]:

    Returns:

    """
    conn.execute(
        "INSERT OR REPLACE INTO orders("
        "id, ts, symbol, side, type, qty, price, status, reason"
        ") VALUES(?,?,?,?,?,?,?,?,?)",
        (
            row["id"],
            row["ts"],
            row["symbol"],
            row["side"],
            row["type"],
            row["qty"],
            row.get("price"),
            row.get("status", "pending"),
            row.get("reason"),
        ),
    )


def log_event(conn: sqlite3.Connection, level: str, component: str, message: str) -> None:
    """Ajoute un evenement dans la table events.

    Args:
      conn: Connexion SQLite.
      level: Niveau de log (INFO, WARNING, ERROR, etc.).
      component: Nom du composant ou module.
      message: Texte descriptif de l'evenement.
      conn: sqlite3.Connection:
      level: str:
      component: str:
      message: str:

    Returns:

    """
    conn.execute(
        "INSERT INTO events(ts, level, component, message) VALUES(?,?,?,?)",
        (int(time.time() * 1000), level, component, message),
    )
