"""Tests for the MQTT message dispatcher in main.py (Phase 20 audit fix H2 + 23)."""
import time
from unittest.mock import patch

import pytest

import db
import live_state

# Pool used throughout the suite; base topic matches the incoming concrete
# topic ``home/Pool/pool/<suffix>`` so the wildcard subscription <base>/+ picks
# every test message up.
_POOL = "Pool"
_BASE = "home/Pool/pool"


@pytest.fixture
def pump_handlers(monkeypatch):
    """Inject a fresh LiveState and base-topic map; close DB to start clean."""
    import main

    db.close()
    state = live_state.LiveState(ring_size=5, stale_after_seconds=600)
    monkeypatch.setattr(main, "_state", state, raising=False)
    monkeypatch.setattr(main, "_base_to_pool_map", {_BASE: _POOL}, raising=False)
    return main, state


@pytest.fixture
def ble_handlers(monkeypatch):
    """Inject a fresh LiveState and base-topic map."""
    import main

    db.close()
    state = live_state.LiveState(ring_size=5, stale_after_seconds=600)
    monkeypatch.setattr(main, "_state", state, raising=False)
    monkeypatch.setattr(main, "_base_to_pool_map", {_BASE: _POOL}, raising=False)
    return main, state


def test_strict_bool_accepts_real_bool():
    from main import _strict_bool

    assert _strict_bool(True, "mainPump") is True
    assert _strict_bool(False, "mainPump") is False


def test_strict_bool_accepts_int_0_1():
    from main import _strict_bool

    assert _strict_bool(0, "mainPump") is False
    assert _strict_bool(1, "mainPump") is True


def test_strict_bool_accepts_truthy_strings():
    from main import _strict_bool

    for s in ("true", "TRUE", "on", "yes", "1"):
        assert _strict_bool(s, "mainPump") is True, f"expected True for {s!r}"


def test_strict_bool_accepts_falsy_strings():
    from main import _strict_bool

    for s in ("false", "FALSE", "off", "no", "0", ""):
        assert _strict_bool(s, "mainPump") is False, f"expected False for {s!r}"


def test_strict_bool_rejects_non_zero_one_numbers():
    from main import _strict_bool

    for v in (2, -1, 0.5):
        with pytest.raises(ValueError):
            _strict_bool(v, "mainPump")


def test_strict_bool_rejects_arbitrary_strings():
    from main import _strict_bool

    for s in ("hello", "maybe", "01"):
        with pytest.raises(ValueError):
            _strict_bool(s, "mainPump")


def test_strict_bool_rejects_none_and_non_string():
    from main import _strict_bool

    with pytest.raises(ValueError):
        _strict_bool(None, "mainPump")
    with pytest.raises(ValueError):
        _strict_bool(["true"], "mainPump")
    with pytest.raises(ValueError):
        _strict_bool({"v": True}, "mainPump")


def test_handle_pool_message_pump_string_false_means_off(pump_handlers):
    """Regression test for H2: ``"false"`` as a string must mean OFF, not ON.

    Even when the message is published under a non-pump topic suffix
    (``/ble-yc01``), the JSON content is what matters."""
    main, state = pump_handlers
    msg = {"mainPump": "false", "solarPump": "true", "time": 1234567890}
    main._handle_pool_message(f"{_BASE}/ble-yc01", msg)
    snap = state.get_snapshot(_POOL)
    assert snap["pump"]["main"]["running"] is False
    assert snap["pump"]["solar"]["running"] is True


def test_handle_pool_message_unknown_topic_is_dropped(pump_handlers):
    main, state = pump_handlers
    msg = {"mainPump": True}
    main._handle_pool_message("home/Other/pool/pump", msg)
    snap = state.get_snapshot(_POOL)
    assert snap["pump"]["main"]["running"] is None


def test_handle_pool_message_invalid_value_is_logged_and_ignored(pump_handlers):
    main, state = pump_handlers
    msg = {"mainPump": "maybe", "solarPump": True}
    with patch("main.log") as log:
        main._handle_pool_message(f"{_BASE}/pump", msg)
        assert log.warning.called
    snap = state.get_snapshot(_POOL)
    assert snap["pump"]["main"]["running"] is None
    assert snap["pump"]["solar"]["running"] is True


def test_handle_pool_message_missing_time_uses_now(pump_handlers):
    main, state = pump_handlers
    before = int(time.time())
    main._handle_pool_message(f"{_BASE}/pump", {"mainPump": True})
    after = int(time.time())
    snap = state.get_snapshot(_POOL)
    assert snap["pump"]["main"]["since"] is not None
    assert before <= snap["pump"]["main"]["since"] <= after


def test_handle_pool_message_explicit_zero_timestamp_is_kept(pump_handlers):
    """L1 fix: ``time: 0`` (epoch) must NOT be replaced with the current time
    by the falsy-zero-or fallback."""
    main, state = pump_handlers
    main._handle_pool_message(f"{_BASE}/pump", {"mainPump": True, "time": 0})
    snap = state.get_snapshot(_POOL)
    assert snap["pump"]["main"]["since"] == 0


def test_handle_pool_message_partial_pump_only_main(pump_handlers):
    """A payload carrying only mainPump must update only the main pump."""
    main, state = pump_handlers
    main._handle_pool_message(f"{_BASE}/pump", {"mainPump": True})
    snap = state.get_snapshot(_POOL)
    assert snap["pump"]["main"]["running"] is True
    assert snap["pump"]["solar"]["running"] is None


def test_handle_pool_message_partial_pump_only_solar(pump_handlers):
    main, state = pump_handlers
    main._handle_pool_message(f"{_BASE}/pump", {"solarPump": True})
    snap = state.get_snapshot(_POOL)
    assert snap["pump"]["main"]["running"] is None
    assert snap["pump"]["solar"]["running"] is True


def test_handle_pool_message_ble_records_metrics(ble_handlers):
    main, state = ble_handlers
    msg = {"temp": 24.5, "pH": 7.2, "cl": 0.7, "time": 1234567890}
    main._handle_pool_message(f"{_BASE}/ble-yc01", msg)
    snap = state.get_snapshot(_POOL)
    assert snap["temp"] == 24.5
    assert snap["pH"] == 7.2
    assert snap["cl"] == 0.7
    assert snap["ts"] == 1234567890


def test_handle_pool_message_ble_skips_unknown_metric(ble_handlers):
    main, state = ble_handlers
    main._handle_pool_message(f"{_BASE}/ble-yc01", {"nitrogen": 99.9, "time": 1})
    snap = state.get_snapshot(_POOL)
    assert snap["ts"] == 0


def test_handle_pool_message_ble_logs_bad_value_and_continues(ble_handlers):
    main, state = ble_handlers
    msg = {"temp": "not-a-number", "pH": 7.2, "cl": 0.7, "time": 1}
    with patch("main.log") as log:
        main._handle_pool_message(f"{_BASE}/ble-yc01", msg)
        assert log.warning.called
    snap = state.get_snapshot(_POOL)
    assert snap["temp"] is None
    assert snap["pH"] == 7.2
    assert snap["cl"] == 0.7


def test_handle_pool_message_unknown_pool_in_map_is_dropped(ble_handlers, monkeypatch):
    """M1: even if the base-topic map somehow contains a pool name that is
    not in POOL_NAMES, the handler must refuse to write state for it. This is
    defense-in-depth against memory-exhaustion via a poisoned map."""
    import main
    main._base_to_pool_map = {"home/EVIL/pool": "NotInPoolList"}
    main._handle_pool_message("home/EVIL/pool/ble-yc01", {"temp": 99.9, "time": 1})
    assert "NotInPoolList" not in main._state._metrics


def test_handle_pool_message_unknown_pump_pool_in_map_is_dropped(monkeypatch):
    """M1: same guard for pump payloads."""
    import main
    db.close()
    state = live_state.LiveState(ring_size=5, stale_after_seconds=600)
    monkeypatch.setattr(main, "_state", state, raising=False)
    monkeypatch.setattr(main, "_base_to_pool_map", {"home/EVIL/pool": "NotInPoolList"}, raising=False)
    main._handle_pool_message("home/EVIL/pool/pump", {"mainPump": True})
    assert "NotInPoolList" not in main._state._pumps


def test_handle_pool_message_ignores_event_payload(pump_handlers):
    """Event messages are not subscribed-to, but the handler must not
    misclassify them as pumps if they ever arrive on the wildcard."""
    main, state = pump_handlers
    msg = {"time": 1, "name": _POOL, "eventType": "chlorine"}
    main._handle_pool_message(f"{_BASE}/event", msg)
    snap = state.get_snapshot(_POOL)
    assert snap["pump"]["main"]["running"] is None
    assert snap["pump"]["solar"]["running"] is None
    assert snap["temp"] is None


def test_handle_pool_message_mixed_ble_and_pump(pump_handlers):
    """A single payload carrying both metrics and pump fields must update
    both kinds of state."""
    main, state = pump_handlers
    msg = {"time": 1, "temp": 24.5, "mainPump": True}
    main._handle_pool_message(f"{_BASE}/pump", msg)
    snap = state.get_snapshot(_POOL)
    assert snap["temp"] == 24.5
    assert snap["pump"]["main"]["running"] is True


def test_pump_event_throttle_limits_db_writes(monkeypatch, tmp_path):
    """M2: rapid pump publishes (faster than LIVE_PUMP_MIN_EVENT_INTERVAL)
    must not flood the pump_events table."""
    import main
    db.close()
    db.init_db(str(tmp_path / "throttle.db"))
    monkeypatch.setattr(main, "LIVE_PUMP_MIN_EVENT_INTERVAL", 60, raising=False)
    state = live_state.LiveState(ring_size=5, stale_after_seconds=600)
    monkeypatch.setattr(main, "_state", state, raising=False)
    monkeypatch.setattr(main, "_base_to_pool_map", {_BASE: _POOL}, raising=False)
    monkeypatch.setattr(main, "_pump_event_throttle", {}, raising=False)

    t0 = 1_000_000
    for i in range(5):
        main._handle_pool_message(f"{_BASE}/pump", {"mainPump": i % 2 == 0, "time": t0})
    snap = state.get_snapshot(_POOL)
    assert snap["pump"]["main"]["running"] is True
    events = db.get_pump_events(_POOL, 0)
    assert len(events) == 1  # only the first one was persisted


def test_pump_event_throttle_resets_after_interval(monkeypatch, tmp_path):
    """M2: after the interval elapses (wall-clock), a new event is persisted."""
    import main
    db.close()
    db.init_db(str(tmp_path / "throttle2.db"))
    monkeypatch.setattr(main, "LIVE_PUMP_MIN_EVENT_INTERVAL", 1, raising=False)
    state = live_state.LiveState(ring_size=5, stale_after_seconds=600)
    monkeypatch.setattr(main, "_state", state, raising=False)
    monkeypatch.setattr(main, "_base_to_pool_map", {_BASE: _POOL}, raising=False)
    monkeypatch.setattr(main, "_pump_event_throttle", {}, raising=False)

    # Simulate time advancing by 5s between publish 2 and 3.
    throttle_calls = iter([0, 5, 10])
    monkeypatch.setattr(main, "_should_persist_pump_event",
                        lambda pool, pump_name, now: (next(throttle_calls) >= 1))

    main._handle_pool_message(f"{_BASE}/pump", {"mainPump": True})
    main._handle_pool_message(f"{_BASE}/pump", {"mainPump": False})
    main._handle_pool_message(f"{_BASE}/pump", {"mainPump": True})
    events = db.get_pump_events(_POOL, 0)
    assert len(events) == 2


def test_is_valid_pool_name_accepts_normal_names():
    from main import _is_valid_pool_name

    assert _is_valid_pool_name("Pool") is True
    assert _is_valid_pool_name("Pool 1") is True
    assert _is_valid_pool_name("My-Pool_2") is True
    assert _is_valid_pool_name("A" * 32) is True


def test_is_valid_pool_name_rejects_mqtt_wildcards():
    """L3: pool names that contain MQTT wildcards must be rejected at startup
    so they cannot poison the subscription map."""
    from main import _is_valid_pool_name

    for bad in ("Pool+", "Pool#", "Pool$", "+", "#", "$SYS", "a/b", ""):
        assert _is_valid_pool_name(bad) is False, f"expected reject for {bad!r}"


def test_is_valid_pool_name_rejects_too_long():
    from main import _is_valid_pool_name

    assert _is_valid_pool_name("A" * 33) is False


def test_is_valid_base_topic_accepts_normal():
    from main import _is_valid_base_topic

    for ok in ("home/pool1", "home/H32/pool", "esp32/ble", "a", "a_b-c/d_e-f"):
        assert _is_valid_base_topic(ok) is True, f"expected accept for {ok!r}"


def test_is_valid_base_topic_rejects_wildcards():
    from main import _is_valid_base_topic

    for bad in ("", "home/+", "home/#", "$SYS/ble", "home//ble", "/home"):
        assert _is_valid_base_topic(bad) is False, f"expected reject for {bad!r}"


def test_pump_event_not_persisted_for_unknown_pool(monkeypatch, tmp_path):
    """L5 (covered by M1+M2): even if the base-topic map names a pool that is
    not in POOL_NAMES, neither in-memory state nor pump_events must be written."""
    import main
    db.close()
    db.init_db(str(tmp_path / "l5.db"))
    monkeypatch.setattr(main, "_pump_event_throttle", {}, raising=False)
    state = live_state.LiveState(ring_size=5, stale_after_seconds=600)
    monkeypatch.setattr(main, "_state", state, raising=False)
    monkeypatch.setattr(main, "_base_to_pool_map", {"home/Other/pool": "GhostPool"}, raising=False)

    main._handle_pool_message("home/Other/pool/pump", {"mainPump": True, "time": 1})
    # In-memory state untouched
    assert state.get_snapshot("GhostPool")["pump"]["main"]["running"] is None
    # And nothing was persisted to pump_events
    assert db.get_pump_events("GhostPool", 0) == []
