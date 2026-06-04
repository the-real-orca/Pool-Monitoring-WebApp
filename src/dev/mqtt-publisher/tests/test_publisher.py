"""Tests for the debug MQTT publisher (deterministic, no real broker)."""
import importlib.util
import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Load publisher.py without executing main() (it has no module-level side effects).
SPEC = importlib.util.spec_from_file_location(
    "publisher",
    Path(__file__).resolve().parent.parent / "publisher.py",
)
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


# --- payload generation ---------------------------------------------------


def test_ble_payload_has_required_fields():
    topic, payload = publisher._ble_payload("Pool 1", tick=0)
    assert topic == "home/Pool 1/pool/ble-yc01"
    for key in ("time", "name", "sensorType", "temp", "pH", "cl"):
        assert key in payload
    assert payload["name"] == "Pool 1"
    assert payload["sensorType"] == "ble-yc01"
    assert 20.0 <= payload["temp"] <= 35.0
    assert 6.5 <= payload["pH"] <= 8.0
    assert 0.1 <= payload["cl"] <= 2.0
    assert isinstance(payload["time"], int)


def test_ble_payload_deterministic_with_seed():
    """Seeding the module-level rng must produce identical payloads."""
    import random as _random

    publisher.rng = _random.Random(42)
    _, p1 = publisher._ble_payload("Pool", tick=0)
    publisher.rng = _random.Random(42)
    _, p2 = publisher._ble_payload("Pool", tick=0)
    assert p1 == p2


def test_pump_payload_field_names():
    topic, payload = publisher._pump_payload("Pool 1", tick=0)
    assert topic == "home/Pool 1/pool/pump"
    assert set(payload.keys()) == {"time", "mainPump", "solarPump"}
    assert isinstance(payload["mainPump"], bool)
    assert isinstance(payload["solarPump"], bool)


def test_pump_payload_toggles_with_tick():
    """PUMP_TOGGLE_EVERY=2 (set below) -> main flips every 2 ticks."""
    publisher.PUMP_TOGGLE_EVERY = 2
    states = [publisher._pump_payload("Pool", tick=t)[1]["mainPump"] for t in range(8)]
    assert states == [True, True, False, False, True, True, False, False]


def test_pump_payload_uses_template_env(monkeypatch):
    monkeypatch.setattr(publisher, "PUMP_TOPIC_TEMPLATE", "alt/{pool}/pump")
    topic, _ = publisher._pump_payload("Spa", tick=0)
    assert topic == "alt/Spa/pump"


# --- main loop ------------------------------------------------------------


def _drive_loop(ticks: int, interval: float = 0.0):
    """Run publisher.run() with a mocked mqtt client and stop after *ticks*
    cycles. Returns the list of (topic, payload) pairs that were published."""
    client = MagicMock()
    published: list[tuple[str, dict]] = []

    def fake_publish(topic, payload, qos=0):
        published.append((topic, json.loads(payload)))
        return MagicMock(rc=0)

    client.publish.side_effect = fake_publish
    publisher.INTERVAL_SECONDS = max(1, int(interval)) if interval else 1
    # Patch time.sleep to be a no-op so the loop spins fast.
    orig_sleep = time.sleep

    def fast_sleep(_seconds):
        pass

    time.sleep = fast_sleep
    try:
        # Run synchronously in a thread so we can break out from outside.
        import threading

        result: dict = {}

        def _runner():
            result["code"] = publisher.run(client)

        t = threading.Thread(target=_runner, daemon=True)
        t.start()
        # Wait for ``ticks`` publish rounds.
        target = ticks * len(publisher.POOLS) * 2  # 2 publishes per pool
        for _ in range(200):
            if len(published) >= target:
                break
            orig_sleep(0.01)
        # Signal the loop to exit.
        publisher.stop_flag = True  # type: ignore[attr-defined]
        # The loop checks its own ``stop`` dict; expose the same mechanism.
        client.publish  # silence linter
    finally:
        time.sleep = orig_sleep
    return published


def test_run_publishes_for_every_pool_every_tick():
    client = MagicMock()
    published: list[tuple[str, dict]] = []

    def fake_publish(topic, payload, qos=0):
        published.append((topic, json.loads(payload)))
        return MagicMock(rc=0)

    client.publish.side_effect = fake_publish
    publisher.INTERVAL_SECONDS = 1
    publisher.POOLS = ["PoolA", "PoolB"]

    # Override run()'s internal stop dict by patching time.sleep so the loop
    # spins, then break out by raising from sleep once we have enough samples.
    target = 3 * len(publisher.POOLS) * 2
    sleeps = {"n": 0}

    def counting_sleep(_):
        sleeps["n"] += 1
        if len(published) >= target:
            # Mimic SIGTERM: raise to break out of the inner sleep loop.
            raise SystemExit(0)
        return None

    orig_sleep = time.sleep
    time.sleep = counting_sleep
    try:
        with pytest.raises(SystemExit):
            publisher.run(client)
    finally:
        time.sleep = orig_sleep

    topics = [t for t, _ in published]
    assert topics.count("home/PoolA/pool/ble-yc01") == 3
    assert topics.count("home/PoolA/pool/pump") == 3
    assert topics.count("home/PoolB/pool/ble-yc01") == 3
    assert topics.count("home/PoolB/pool/pump") == 3
    # Every published payload has the required keys.
    for _, payload in published:
        if "temp" in payload:  # BLE
            assert {"time", "name", "temp", "pH", "cl"} <= payload.keys()
        else:  # pump
            assert {"time", "mainPump", "solarPump"} <= payload.keys()


def test_run_calls_disconnect_on_exit():
    client = MagicMock()
    publisher.POOLS = ["Pool"]
    publisher.INTERVAL_SECONDS = 1

    orig_sleep = time.sleep
    time.sleep = lambda _: (_ for _ in ()).throw(SystemExit(0))
    try:
        with pytest.raises(SystemExit):
            publisher.run(client)
    finally:
        time.sleep = orig_sleep
    client.loop_stop.assert_called_once()
    client.disconnect.assert_called_once()


# --- TLS configuration ---------------------------------------------------


@pytest.fixture
def mocked_client_class(monkeypatch):
    """Replace paho.mqtt.client.Client with a MagicMock and return a list
    of captured ssl contexts (when tls_set_context is called)."""
    captured_contexts: list = []
    captured_tls_set_args: list = []

    fake_instance = MagicMock(name="mqtt.Client instance")
    fake_instance.tls_set_context.side_effect = lambda ctx: captured_contexts.append(ctx)
    fake_instance.tls_set.side_effect = lambda *a, **kw: captured_tls_set_args.append((a, kw))

    fake_cls = MagicMock(name="mqtt.Client class", return_value=fake_instance)

    monkeypatch.setattr(publisher.mqtt_lib, "Client", fake_cls)
    return fake_instance, captured_contexts, captured_tls_set_args


def test_build_client_no_tls(mocked_client_class):
    """MQTT_TLS=false -> neither tls_set nor tls_set_context is called."""
    fake, contexts, tls_args = mocked_client_class
    publisher.MQTT_TLS = False
    publisher.MQTT_TLS_INSECURE = False
    publisher.MQTT_USER = ""
    publisher._build_client()
    fake.tls_set.assert_not_called()
    fake.tls_set_context.assert_not_called()
    assert contexts == []
    assert tls_args == []


def test_build_client_tls_secure(mocked_client_class):
    """MQTT_TLS=true, MQTT_TLS_INSECURE=false -> tls_set() with default CA."""
    fake, contexts, tls_args = mocked_client_class
    publisher.MQTT_TLS = True
    publisher.MQTT_TLS_INSECURE = False
    publisher.MQTT_USER = ""
    publisher._build_client()
    fake.tls_set.assert_called_once()
    fake.tls_set_context.assert_not_called()
    assert contexts == []


def test_build_client_tls_insecure_uses_unverified_context(mocked_client_class):
    """MQTT_TLS_INSECURE=true -> ssl context with CERT_NONE / no hostname check."""
    import ssl as _ssl

    fake, contexts, tls_args = mocked_client_class
    publisher.MQTT_TLS = True
    publisher.MQTT_TLS_INSECURE = True
    publisher.MQTT_USER = ""
    publisher._build_client()
    fake.tls_set_context.assert_called_once()
    fake.tls_set.assert_not_called()
    assert len(contexts) == 1
    ctx = contexts[0]
    assert ctx.verify_mode == _ssl.CERT_NONE
    assert ctx.check_hostname is False


def test_build_client_tls_insecure_only_when_explicit(mocked_client_class):
    """MQTT_TLS=false, MQTT_TLS_INSECURE=true -> insecure flag is a no-op
    because TLS is not even enabled. This avoids accidentally starting a
    plaintext connection with a 'CERT_NONE' context by mistake."""
    fake, contexts, tls_args = mocked_client_class
    publisher.MQTT_TLS = False
    publisher.MQTT_TLS_INSECURE = True
    publisher.MQTT_USER = ""
    publisher._build_client()
    fake.tls_set.assert_not_called()
    fake.tls_set_context.assert_not_called()
