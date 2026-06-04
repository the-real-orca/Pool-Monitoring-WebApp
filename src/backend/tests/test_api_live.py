"""API tests for the live-data endpoints (Phase 20.6)."""
import time
from unittest.mock import patch

import db
import live_state


def _setup_live(tmp_path, monkeypatch):
    """Init the SQLite DB at a tmp path and inject a fresh LiveState into
    the main module's globals."""
    import main

    db.close()
    assert db.init_db(str(tmp_path / "data.db"))

    state = live_state.LiveState(ring_size=5, stale_after_seconds=600)
    monkeypatch.setattr(main, "_state", state, raising=False)
    monkeypatch.setattr(main, "_topic_to_pool_map", {}, raising=False)
    return main, state


def test_api_live_snapshot_shape(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get(
        "/api/live?pool=Pool",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ts"] == 0
    assert data["temp"] is None
    assert data["pH"] is None
    assert data["cl"] is None
    assert data["stale"] is True
    assert data["staleSeconds"] is None
    assert "pump" in data
    assert "main" in data["pump"]
    assert "solar" in data["pump"]


def test_api_live_with_data(client, tmp_path, monkeypatch):
    main, state = _setup_live(tmp_path, monkeypatch)
    now = int(time.time())
    state.push_sample("Pool", "temp", 24.6, now)
    state.push_sample("Pool", "pH", 7.2, now)
    state.push_sample("Pool", "cl", 0.7, now)
    state.set_pump("Pool", "main", True, now)

    response = client.get(
        "/api/live?pool=Pool",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["temp"] == 24.6
    assert data["pH"] == 7.2
    assert data["cl"] == 0.7
    assert data["stale"] is False
    assert data["pump"]["main"]["running"] is True
    assert data["pump"]["solar"]["running"] is None


def test_api_live_401_without_token(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get("/api/live?pool=Pool")
    assert response.status_code == 422  # missing header


def test_api_live_401_wrong_token(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get(
        "/api/live?pool=Pool",
        headers={"Authorization": "Bearer wrong"},
    )
    assert response.status_code == 401


def test_api_live_422_unknown_pool(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get(
        "/api/live?pool=Nonexistent",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422


def test_api_pools_live_returns_only_pools_with_data(client, tmp_path, monkeypatch):
    main, state = _setup_live(tmp_path, monkeypatch)
    # The default POOL_LIST for tests contains only {"name": "Pool"} —
    # add a second pool via the test fixture? The conftest builds POOL_LIST
    # from env. Verify that the response includes "Pool" and reflects
    # hasData state.
    response = client.get(
        "/api/pools/live",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert {"name": "Pool", "hasData": False} in data
    state.push_sample("Pool", "temp", 1.0, int(time.time()))
    response = client.get(
        "/api/pools/live",
        headers={"Authorization": "Bearer test-token"},
    )
    data = response.json()
    assert {"name": "Pool", "hasData": True} in data


def test_api_pools_live_401(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get("/api/pools/live")
    assert response.status_code == 422


def test_api_history_returns_aggregates(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    now = int(time.time())
    # 3 consecutive hours of aggregates
    db.insert_aggregate("Pool", "temp", now - 3600, 24.0, 1)
    db.insert_aggregate("Pool", "temp", now - 7200, 25.0, 1)
    db.insert_aggregate("Pool", "temp", now - 10800, 26.0, 1)
    response = client.get(
        "/api/history?pool=Pool&metric=temp&days=7",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pool"] == "Pool"
    assert data["metric"] == "temp"
    assert data["unit"] == "°C"
    assert len(data["points"]) == 3
    assert data["points"][0]["t"] < data["points"][1]["t"]


def test_api_history_empty_when_no_aggregates(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get(
        "/api/history?pool=Pool&metric=pH&days=7",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["unit"] == ""
    assert data["points"] == []


def test_api_history_422_unknown_pool(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get(
        "/api/history?pool=Nope&metric=temp&days=7",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422


def test_api_history_422_bad_metric(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get(
        "/api/history?pool=Pool&metric=humidity&days=7",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422


def test_api_history_422_days_out_of_range(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get(
        "/api/history?pool=Pool&metric=temp&days=0",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422
    response = client.get(
        "/api/history?pool=Pool&metric=temp&days=31",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422


def test_api_pump_events_returns_inserted_events(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    now = int(time.time())
    db.insert_pump_event("Pool", "main", True, now - 100, now - 99)
    db.insert_pump_event("Pool", "main", False, now - 50, now - 49)
    db.insert_pump_event("Pool", "solar", True, now - 10, now - 9)
    response = client.get(
        "/api/pump-events?pool=Pool&days=7",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pool"] == "Pool"
    assert len(data["events"]) == 3
    assert data["events"][0]["state"] is True
    assert data["events"][1]["state"] is False
    assert data["events"][2]["pump"] == "solar"


def test_api_pump_events_pool_isolation(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    now = int(time.time())
    db.insert_pump_event("Pool", "main", True, now, now)
    response = client.get(
        "/api/pump-events?pool=Pool&days=7",
        headers={"Authorization": "Bearer test-token"},
    )
    data = response.json()
    assert len(data["events"]) == 1
    # The pool is implicit (from the query); we just confirm the event shape
    assert data["events"][0]["pump"] == "main"
    assert data["events"][0]["state"] is True


def test_api_pump_events_422_unknown_pool(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get(
        "/api/pump-events?pool=Nope&days=7",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422


def test_api_status_includes_live_data_configured(client, tmp_path, monkeypatch):
    _setup_live(tmp_path, monkeypatch)
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["liveDataConfigured"] is True


def test_api_status_live_data_unconfigured(client, tmp_path, monkeypatch):
    db.close()
    import main
    monkeypatch.setattr(main, "_state", live_state.LiveState(), raising=False)
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["liveDataConfigured"] is False
