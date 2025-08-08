from __future__ import annotations
import sqlite3
import os
import time
from typing import Dict, Any

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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None)
    conn.executescript(SCHEMA)
    return conn


def insert_order(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO orders(id, ts, symbol, side, type, qty, price, status, reason) VALUES(?,?,?,?,?,?,?,?,?)",
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
    conn.execute(
        "INSERT INTO events(ts, level, component, message) VALUES(?,?,?,?)",
        (int(time.time() * 1000), level, component, message),
    )
