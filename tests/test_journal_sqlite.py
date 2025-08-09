from __future__ import annotations

from pathlib import Path

from dia_core.portfolio import journal


def test_journal_insert_order(tmp_path: Path) -> None:
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
