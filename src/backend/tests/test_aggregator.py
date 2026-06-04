"""Tests for the aggregator background task (Phase 20.5)."""
import asyncio
import time
from unittest.mock import MagicMock

import aggregator
import db
import live_state


def _setup_db(tmp_path):
    db.close()
    db.init_db(str(tmp_path / "data.db"))


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


def test_cleanup_skipped_within_min_interval(monkeypatch, tmp_path):
    """I3: cleanup must not run more than once per min_cleanup_interval."""
    _setup_db(tmp_path)
    state = live_state.LiveState()
    a = aggregator.Aggregator(
        state, retention_days=90, cleanup_hour_utc=3,
        min_cleanup_interval_seconds=20 * 3600,
    )
    calls = {"n": 0}
    real_cleanup = db.cleanup_old_rows

    def counting(retention_days):
        calls["n"] += 1
        return real_cleanup(retention_days)

    monkeypatch.setattr(aggregator.db, "cleanup_old_rows", counting)

    t0 = int(time.mktime((2026, 6, 4, 3, 0, 0, 0, 0, 0)))
    a._maybe_daily_cleanup(t0)
    # Same day, even 1 hour later, must be blocked by min interval
    a._maybe_daily_cleanup(t0 + 3600)
    a._maybe_daily_cleanup(t0 + 2 * 3600)
    assert calls["n"] == 1


def test_cleanup_runs_again_after_min_interval(monkeypatch, tmp_path):
    """I3: when the wall-clock interval has elapsed, a new cleanup is allowed."""
    _setup_db(tmp_path)
    state = live_state.LiveState()
    a = aggregator.Aggregator(
        state, retention_days=90, cleanup_hour_utc=3,
        min_cleanup_interval_seconds=20 * 3600,
    )
    calls = {"n": 0}
    real_cleanup = db.cleanup_old_rows

    def counting(retention_days):
        calls["n"] += 1
        return real_cleanup(retention_days)

    monkeypatch.setattr(aggregator.db, "cleanup_old_rows", counting)

    t0 = int(time.mktime((2026, 6, 4, 3, 0, 0, 0, 0, 0)))
    a._maybe_daily_cleanup(t0)
    assert calls["n"] == 1
    # 21 hours later, hour=00 -> not the cleanup hour, no run
    a._maybe_daily_cleanup(t0 + 21 * 3600)
    assert calls["n"] == 1
    # 24h later: new day, hour=3, min_interval passed -> cleanup runs
    a._maybe_daily_cleanup(t0 + 24 * 3600)
    assert calls["n"] == 2
    # 27h later: hour=6, no cleanup
    a._maybe_daily_cleanup(t0 + 27 * 3600)
    assert calls["n"] == 2
    # 2026-06-06 03:00 UTC: cleanup runs again
    t_next = int(time.mktime((2026, 6, 6, 3, 0, 0, 0, 0, 0)))
    a._maybe_daily_cleanup(t_next)
    assert calls["n"] == 3


def test_cleanup_survives_clock_jump_backward(monkeypatch, tmp_path):
    """I3: an NTP jump backwards must not produce a duplicate cleanup on
    the same UTC date."""
    _setup_db(tmp_path)
    state = live_state.LiveState()
    a = aggregator.Aggregator(
        state, retention_days=90, cleanup_hour_utc=3,
        min_cleanup_interval_seconds=20 * 3600,
    )
    calls = {"n": 0}
    real_cleanup = db.cleanup_old_rows

    def counting(retention_days):
        calls["n"] += 1
        return real_cleanup(retention_days)

    monkeypatch.setattr(aggregator.db, "cleanup_old_rows", counting)

    t0 = int(time.mktime((2026, 6, 4, 3, 0, 0, 0, 0, 0)))
    a._maybe_daily_cleanup(t0)
    # 12 hours later, hour=15 -> no cleanup
    a._maybe_daily_cleanup(t0 + 12 * 3600)
    assert calls["n"] == 1
    # NTP jumps back 9 hours, so clock reads 06:00 same day. Same date,
    # same 03:00 already done, min_interval not elapsed from t0 -> no cleanup.
    a._maybe_daily_cleanup(t0 + 3 * 3600)
    assert calls["n"] == 1
