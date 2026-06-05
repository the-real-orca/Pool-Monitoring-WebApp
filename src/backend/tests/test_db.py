"""Tests for the SQLite persistence layer (Phase 20.2)."""
import sqlite3
import time

import db


def _fresh_db(tmp_path):
    """Reset module state and re-init the DB at a fresh tmp path."""
    db.close()
    assert db.init_db(str(tmp_path / "data.db"))
    return str(tmp_path / "data.db")


def test_init_creates_schema(tmp_path):
    _fresh_db(tmp_path)
    conn = sqlite3.connect(str(tmp_path / "data.db"))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','index') ORDER BY name"
        ).fetchall()
        names = {r[0] for r in rows}
        assert "measurements" in names

        assert "idx_measurements_hour" in names
        assert "idx_pump_events_time" in names
        assert "idx_pump_events_pool_time" in names
    finally:
        conn.close()


def test_init_is_idempotent(tmp_path):
    _fresh_db(tmp_path)
    # Calling init_db again must not raise and must leave schema intact.
    assert db.init_db(str(tmp_path / "data.db"))
    assert db.is_configured()


def test_insert_and_get_aggregate_roundtrip(tmp_path):
    _fresh_db(tmp_path)
    db.insert_aggregate("H32", "temp", 1700000000, 24.6, 5)
    db.insert_aggregate("H32", "pH", 1700000000, 7.2, 4)
    db.insert_aggregate("H32", "temp", 1700003600, 25.1, 6)

    temps = db.get_aggregates("H32", "temp", 0)
    assert len(temps) == 2
    assert temps[0] == {"t": 1700000000, "v": 24.6, "n": 5}
    assert temps[1] == {"t": 1700003600, "v": 25.1, "n": 6}

    phs = db.get_aggregates("H32", "pH", 0)
    assert len(phs) == 1
    assert phs[0]["v"] == 7.2


def test_get_aggregates_since_filter(tmp_path):
    _fresh_db(tmp_path)
    db.insert_aggregate("H32", "temp", 1000, 20.0, 1)
    db.insert_aggregate("H32", "temp", 2000, 21.0, 1)
    db.insert_aggregate("H32", "temp", 3000, 22.0, 1)
    out = db.get_aggregates("H32", "temp", 2000)
    assert [r["t"] for r in out] == [2000, 3000]


def test_aggregate_upsert_replaces(tmp_path):
    """Inserting twice for the same (pool, metric, hour_start) is a no-op
    overwrite — the last value wins."""
    _fresh_db(tmp_path)
    db.insert_aggregate("H32", "temp", 1700000000, 24.0, 1)
    db.insert_aggregate("H32", "temp", 1700000000, 26.0, 9)
    rows = db.get_aggregates("H32", "temp", 0)
    assert len(rows) == 1
    assert rows[0]["v"] == 26.0
    assert rows[0]["n"] == 9


def test_insert_and_get_pump_event_roundtrip(tmp_path):
    _fresh_db(tmp_path)
    db.insert_pump_event("H32", "main", True, 1000, 1005)
    db.insert_pump_event("H32", "main", False, 2000, 2005)
    events = db.get_pump_events("H32", 0)
    assert len(events) == 2
    assert events[0]["pump"] == "main"
    assert events[0]["state"] is True
    assert events[0]["time"] == 1000
    assert events[0]["received_at"] == 1005
    assert events[1]["state"] is False


def test_pump_events_pool_isolation(tmp_path):
    _fresh_db(tmp_path)
    db.insert_pump_event("A", "main", True, 1, 1)
    db.insert_pump_event("B", "main", True, 2, 2)
    assert len(db.get_pump_events("A", 0)) == 1
    assert len(db.get_pump_events("B", 0)) == 1
    assert db.get_pump_events("C", 0) == []


def test_cleanup_old_rows_deletes_by_retention(tmp_path):
    _fresh_db(tmp_path)
    now = int(time.time())
    old = now - 100 * 86400   # 100 days ago
    recent = now - 5 * 86400  # 5 days ago
    db.insert_aggregate("H32", "temp", old, 20.0, 1)
    db.insert_aggregate("H32", "temp", recent, 21.0, 1)
    db.insert_pump_event("H32", "main", True, old, old)
    db.insert_pump_event("H32", "main", False, recent, recent)

    deleted = db.cleanup_old_rows(90)
    assert deleted == 2

    assert len(db.get_aggregates("H32", "temp", 0)) == 1
    assert len(db.get_pump_events("H32", 0)) == 1


def test_is_configured_and_db_path(tmp_path):
    db.close()
    assert not db.is_configured()
    p = str(tmp_path / "data.db")
    assert db.init_db(p)
    assert db.is_configured()
    assert db.db_path() == p


def test_wal_mode_is_set(tmp_path):
    _fresh_db(tmp_path)
    conn = sqlite3.connect(str(tmp_path / "data.db"))
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"
    finally:
        conn.close()
