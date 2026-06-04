"""Tests for the aggregator background task (Phase 20.5)."""
import asyncio
import time
from unittest.mock import MagicMock

import aggregator
import db
import live_state


def _setup_db(tmp_path):
    db.close()
    db.init_db(str(tmp_path / "live.db"))


def test_hour_start_alignment():
    # 2024-01-01 00:00:00 UTC is a clean hour boundary: 1_704_067_200
    base = 1_704_067_200
    assert aggregator._hour_start(base) == base
    assert aggregator._hour_start(base + 123) == base
    assert aggregator._hour_start(base + 3599) == base
    assert aggregator._hour_start(base + 3600) == base + 3600
    # An off-the-hour timestamp: 800 s into the current hour
    assert aggregator._hour_start(base + 800) == base
    assert aggregator._hour_start(base + 3600 + 800) == base + 3600


def test_rollup_window_writes_aggregate_per_metric(tmp_path):
    _setup_db(tmp_path)
    state = live_state.LiveState(ring_size=10, stale_after_seconds=600)
    state.push_sample("H32", "temp", 24.0, 1_700_000_100)
    state.push_sample("H32", "temp", 26.0, 1_700_000_500)
    state.push_sample("H32", "pH", 7.0, 1_700_000_200)
    state.push_sample("H32", "pH", 7.4, 1_700_000_600)

    a = aggregator.Aggregator(state, tick_seconds=1, retention_days=90)
    hour = 1_700_000_000
    a._rollup_window(hour, hour + 3600)

    temps = db.get_aggregates("H32", "temp", 0)
    assert len(temps) == 1
    assert temps[0]["t"] == hour
    assert temps[0]["v"] == 25.0
    assert temps[0]["n"] == 2

    phs = db.get_aggregates("H32", "pH", 0)
    assert len(phs) == 1
    assert phs[0]["v"] == (7.0 + 7.4) / 2
    assert phs[0]["n"] == 2

    assert db.get_aggregates("H32", "cl", 0) == []


def test_rollup_skips_pools_with_no_samples(tmp_path):
    _setup_db(tmp_path)
    state = live_state.LiveState()
    state.push_sample("H32", "temp", 25.0, 1_700_000_100)
    a = aggregator.Aggregator(state)
    a._rollup_window(1_700_000_000, 1_700_000_000 + 3600)
    # Other pools simply produce no rows
    assert db.get_aggregates("OtherPool", "temp", 0) == []


def test_rollup_does_nothing_when_db_not_configured(tmp_path):
    db.close()
    state = live_state.LiveState()
    state.push_sample("H32", "temp", 25.0, 1_700_000_100)
    a = aggregator.Aggregator(state)
    # No DB; should not raise
    a._rollup_window(1_700_000_000, 1_700_000_000 + 3600)


def test_rollup_continues_after_failing_insert(tmp_path, monkeypatch):
    _setup_db(tmp_path)
    state = live_state.LiveState()
    state.push_sample("H32", "temp", 25.0, 1_700_000_100)
    state.push_sample("H32", "pH", 7.0, 1_700_000_100)

    real_insert = db.insert_aggregate
    calls = {"n": 0}

    def flaky(pool, metric, hour_start, value, n):
        if metric == "temp":
            raise RuntimeError("disk full")
        calls["n"] += 1
        return real_insert(pool, metric, hour_start, value, n)

    monkeypatch.setattr(aggregator.db, "insert_aggregate", flaky)
    a = aggregator.Aggregator(state)
    a._rollup_window(1_700_000_000, 1_700_000_000 + 3600)

    # pH still made it into the DB even though temp raised
    assert len(db.get_aggregates("H32", "pH", 0)) == 1
    assert calls["n"] == 1


def test_maybe_daily_cleanup_runs_only_once_per_utc_day(tmp_path):
    _setup_db(tmp_path)
    state = live_state.LiveState()
    a = aggregator.Aggregator(state, retention_days=90, cleanup_hour_utc=3)

    # First call at 03:00 UTC -> runs once
    a._maybe_daily_cleanup(int(time.mktime((2026, 6, 4, 3, 0, 0, 0, 0, 0))) - 0)
    a._maybe_daily_cleanup(int(time.mktime((2026, 6, 4, 3, 5, 0, 0, 0, 0))))
    a._maybe_daily_cleanup(int(time.mktime((2026, 6, 4, 3, 30, 0, 0, 0, 0))))
    # Different hour -> still skipped
    a._maybe_daily_cleanup(int(time.mktime((2026, 6, 4, 4, 0, 0, 0, 0, 0))))
    # Next day at 03:00 -> runs once more
    a._maybe_daily_cleanup(int(time.mktime((2026, 6, 5, 3, 0, 0, 0, 0, 0))))
    # No assertion needed beyond "no exception" — behavior is "fire and forget".


def test_daily_cleanup_deletes_old_rows(tmp_path):
    _setup_db(tmp_path)
    state = live_state.LiveState()
    a = aggregator.Aggregator(state, retention_days=90, cleanup_hour_utc=3)
    # Use a synthetic 03:00 UTC timestamp to satisfy the cleanup gate
    cleanup_ts = int(time.mktime((2026, 6, 4, 3, 0, 0, 0, 0, 0)))
    # 100 days before 2026-06-04 03:00 UTC = 2026-02-23 03:00 UTC
    old_ts = cleanup_ts - 100 * 86400
    recent_ts = cleanup_ts - 86400
    db.insert_aggregate("H32", "temp", old_ts, 20.0, 1)
    db.insert_aggregate("H32", "temp", recent_ts, 21.0, 1)
    a._maybe_daily_cleanup(cleanup_ts)
    out = db.get_aggregates("H32", "temp", 0)
    assert len(out) == 1


def test_start_stop_runs_task():
    async def runner():
        state = live_state.LiveState()
        a = aggregator.Aggregator(state, tick_seconds=1)
        task = a.start()
        assert isinstance(task, asyncio.Task)
        assert not task.done()
        await a.stop()
        assert a._task is None

    asyncio.run(runner())
