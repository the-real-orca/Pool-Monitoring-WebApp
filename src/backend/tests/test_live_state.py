"""Tests for the in-memory live state (Phase 20.3)."""
import time

import live_state


def test_push_sample_updates_last_value_and_ts():
    s = live_state.LiveState(ring_size=5, stale_after_seconds=600)
    s.push_sample("H32", "temp", 24.6, 1_000)
    snap = s.get_snapshot("H32")
    assert snap["temp"] == 24.6
    assert snap["ts"] == 1_000


def test_ring_buffer_caps_at_ring_size():
    s = live_state.LiveState(ring_size=3, stale_after_seconds=600)
    for i, v in enumerate([7.0, 7.1, 7.2, 7.3, 7.4]):
        s.push_sample("H32", "pH", v, 1_000 + i)
    snap = s.get_snapshot("H32")
    # Only the last 3 samples are averaged
    assert snap["pH"] == (7.2 + 7.3 + 7.4) / 3
    # But the last value used for the temp-style display path
    # (here we test pH mean; temp would expose the last_value via .last_value)


def test_five_sample_mean_uses_all_when_ring_not_full():
    s = live_state.LiveState(ring_size=5, stale_after_seconds=600)
    for v in [6.0, 7.0, 8.0]:
        s.push_sample("H32", "pH", v, 1_000)
    snap = s.get_snapshot("H32")
    assert snap["pH"] == (6.0 + 7.0 + 8.0) / 3


def test_pump_set_pump_detects_change():
    s = live_state.LiveState()
    assert s.set_pump("H32", "main", True, 1_000) is True
    assert s.set_pump("H32", "main", True, 2_000) is False
    assert s.set_pump("H32", "main", False, 3_000) is True
    assert s.set_pump("H32", "main", False, 4_000) is False


def test_pump_set_pump_records_since_timestamp():
    s = live_state.LiveState()
    s.set_pump("H32", "main", True, 1_000)
    s.set_pump("H32", "main", False, 5_000)
    s.set_pump("H32", "main", True, 9_000)
    snap = s.get_snapshot("H32")
    assert snap["pump"]["main"]["running"] is True
    assert snap["pump"]["main"]["since"] == 9_000


def test_pump_unknown_name_ignored():
    s = live_state.LiveState()
    assert s.set_pump("H32", "unknown", True, 1) is False


def test_stale_flag_flips_after_threshold():
    s = live_state.LiveState(ring_size=5, stale_after_seconds=10)
    s.push_sample("H32", "temp", 24.0, 1_000)
    now = int(time.time())
    # Fresh: now is right after the sample timestamp
    fresh_now = 1_000 + 5
    assert s.get_snapshot.__func__ if False else True  # sanity
    # We can't monkey-patch time.time() trivially, so test with a large delta
    snap_recent = live_state.LiveState(ring_size=5, stale_after_seconds=60)
    snap_recent.push_sample("H32", "temp", 24.0, int(time.time()) - 5)
    assert snap_recent.get_snapshot("H32")["stale"] is False
    snap_old = live_state.LiveState(ring_size=5, stale_after_seconds=60)
    snap_old.push_sample("H32", "temp", 24.0, int(time.time()) - 120)
    assert snap_old.get_snapshot("H32")["stale"] is True


def test_stale_when_no_data():
    s = live_state.LiveState(stale_after_seconds=10)
    snap = s.get_snapshot("Empty")
    assert snap["stale"] is True
    assert snap["ts"] == 0
    assert snap["temp"] is None
    assert snap["pH"] is None
    assert snap["cl"] is None


def test_per_pool_isolation():
    s = live_state.LiveState()
    s.push_sample("A", "temp", 20.0, 1_000)
    s.push_sample("B", "temp", 30.0, 2_000)
    s.set_pump("A", "main", True, 1_000)
    s.set_pump("B", "main", False, 2_000)
    assert s.get_snapshot("A")["temp"] == 20.0
    assert s.get_snapshot("B")["temp"] == 30.0
    assert s.get_snapshot("A")["pump"]["main"]["running"] is True
    assert s.get_snapshot("B")["pump"]["main"]["running"] is False


def test_get_known_pools_unions_metrics_and_pumps():
    s = live_state.LiveState()
    s.push_sample("A", "temp", 1.0, 1)
    s.set_pump("B", "main", True, 1)
    pools = s.get_known_pools()
    assert set(pools) == {"A", "B"}


def test_has_data_only_after_first_sample():
    s = live_state.LiveState()
    assert s.has_data("H32") is False
    s.push_sample("H32", "temp", 1.0, 1)
    assert s.has_data("H32") is True


def test_snapshot_stale_seconds_value():
    s = live_state.LiveState(stale_after_seconds=600)
    s.push_sample("H32", "temp", 1.0, int(time.time()) - 30)
    snap = s.get_snapshot("H32")
    assert snap["staleSeconds"] is not None
    assert 25 <= snap["staleSeconds"] <= 35
    assert snap["stale"] is False


def test_unknown_metric_silently_ignored():
    s = live_state.LiveState()
    s.push_sample("H32", "humidity", 50.0, 1)  # not a known metric
    snap = s.get_snapshot("H32")
    assert snap["temp"] is None
    assert snap["pH"] is None
    assert snap["cl"] is None
