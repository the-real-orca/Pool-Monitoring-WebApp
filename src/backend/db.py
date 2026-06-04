"""SQLite layer for live-data persistence (Phase 20).

Stores per-hour aggregates of sensor metrics and every pump-state change
observed via the MQTT subscribe path. All writes are serialized through a
module-level ``threading.Lock`` because paho-mqtt callbacks and the FastAPI
request handler may invoke the writers concurrently.
"""
from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
from typing import Any, Iterable

log = logging.getLogger(__name__)

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None
_db_path: str | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS live_aggregates (
    pool          TEXT    NOT NULL,
    metric        TEXT    NOT NULL,
    hour_start    INTEGER NOT NULL,
    value         REAL    NOT NULL,
    sample_count  INTEGER NOT NULL,
    PRIMARY KEY (pool, metric, hour_start)
);
CREATE INDEX IF NOT EXISTS idx_live_aggregates_hour ON live_aggregates(hour_start);

CREATE TABLE IF NOT EXISTS pump_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pool        TEXT    NOT NULL,
    pump        TEXT    NOT NULL,
    state       INTEGER NOT NULL,
    time        INTEGER NOT NULL,
    received_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pump_events_time ON pump_events(time);
CREATE INDEX IF NOT EXISTS idx_pump_events_pool_time ON pump_events(pool, time);
"""


def init_db(path: str) -> bool:
    """Open (or create) the SQLite database at *path* and apply the schema.

    Returns True on success, False if the path is not writable. The connection
    is kept open at module level and reused for all subsequent calls.
    """
    global _conn, _db_path
    if not path:
        log.warning("init_db called with empty path; live-data disabled")
        return False
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(SCHEMA)
    except Exception as e:
        log.error("init_db failed for %s: %s", path, e)
        return False

    with _lock:
        _conn = conn
        _db_path = path
    log.info("Live-data DB initialized at %s", path)
    return True


def _get_conn() -> sqlite3.Connection | None:
    return _conn


def insert_aggregate(pool: str, metric: str, hour_start: int, value: float, n: int) -> None:
    """Upsert one per-hour aggregate. ``INSERT OR REPLACE`` makes duplicate
    writes for the same (pool, metric, hour_start) a no-op for callers that
    do not care about overwriting."""
    conn = _get_conn()
    if conn is None:
        return
    with _lock:
        conn.execute(
            "INSERT OR REPLACE INTO live_aggregates (pool, metric, hour_start, value, sample_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (pool, metric, hour_start, value, n),
        )


def insert_pump_event(pool: str, pump: str, state: bool, ts: int, received_at: int) -> None:
    conn = _get_conn()
    if conn is None:
        return
    with _lock:
        conn.execute(
            "INSERT INTO pump_events (pool, pump, state, time, received_at) VALUES (?, ?, ?, ?, ?)",
            (pool, pump, 1 if state else 0, ts, received_at),
        )


def get_aggregates(pool: str, metric: str, since_ts: int) -> list[dict[str, Any]]:
    conn = _get_conn()
    if conn is None:
        return []
    with _lock:
        cur = conn.execute(
            "SELECT hour_start, value, sample_count FROM live_aggregates "
            "WHERE pool = ? AND metric = ? AND hour_start >= ? ORDER BY hour_start ASC",
            (pool, metric, since_ts),
        )
        return [
            {"t": int(row[0]), "v": float(row[1]), "n": int(row[2])}
            for row in cur.fetchall()
        ]


def get_pump_events(pool: str, since_ts: int) -> list[dict[str, Any]]:
    conn = _get_conn()
    if conn is None:
        return []
    with _lock:
        cur = conn.execute(
            "SELECT id, pool, pump, state, time, received_at FROM pump_events "
            "WHERE pool = ? AND time >= ? ORDER BY time ASC",
            (pool, since_ts),
        )
        return [
            {
                "id": int(row[0]),
                "pool": row[1],
                "pump": row[2],
                "state": bool(row[3]),
                "time": int(row[4]),
                "received_at": int(row[5]),
            }
            for row in cur.fetchall()
        ]


def cleanup_old_rows(retention_days: int) -> int:
    """Delete aggregates and pump events older than *retention_days*. Returns
    the number of rows deleted (aggregates + pump events)."""
    conn = _get_conn()
    if conn is None:
        return 0
    cutoff = int(time.time()) - retention_days * 86400
    with _lock:
        cur_a = conn.execute("DELETE FROM live_aggregates WHERE hour_start < ?", (cutoff,))
        cur_p = conn.execute("DELETE FROM pump_events WHERE time < ?", (cutoff,))
        return cur_a.rowcount + cur_p.rowcount


def is_configured() -> bool:
    return _conn is not None


def db_path() -> str | None:
    return _db_path


def close() -> None:
    global _conn, _db_path
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
            _conn = None
            _db_path = None
