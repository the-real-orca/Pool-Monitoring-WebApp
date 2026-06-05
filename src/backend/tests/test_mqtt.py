"""Tests for the MQTT subscribe path (Phase 20.4)."""
import json
from unittest.mock import MagicMock, patch

import mqtt


def _make_client_mock():
    client = MagicMock()
    client.is_connected.return_value = True
    return client


def test_subscribe_registers_topic():
    mqtt.clear_subscriptions()
    cb = lambda topic, payload: None
    mqtt.subscribe("home/H32/pool/ble-yc01", cb)
    subs = mqtt.subscriptions()
    assert ("home/H32/pool/ble-yc01", cb) in subs
    assert len(subs) == 1


def test_subscribe_while_connected_calls_client_subscribe():
    mqtt.clear_subscriptions()
    client = _make_client_mock()
    with patch.object(mqtt, "_client", client):
        mqtt.subscribe("home/H32/pool/ble-yc01", lambda t, p: None)
    client.subscribe.assert_called_once()
    args = client.subscribe.call_args[0]
    assert args[0] == "home/H32/pool/ble-yc01"


def test_subscribe_while_disconnected_does_not_call_client():
    mqtt.clear_subscriptions()
    client = _make_client_mock()
    client.is_connected.return_value = False
    with patch.object(mqtt, "_client", client):
        mqtt.subscribe("home/H32/pool/pump", lambda t, p: None)
    client.subscribe.assert_not_called()


def test_on_connect_resubscribes_all_topics():
    mqtt.clear_subscriptions()
    cb_a = lambda t, p: None
    cb_b = lambda t, p: None
    mqtt.subscribe("home/A/pool/ble-yc01", cb_a)
    mqtt.subscribe("home/A/pool/pump", cb_b)
    client = _make_client_mock()
    with patch.object(mqtt, "_client", client):
        on_connect = mqtt._make_on_connect()
        # Simulate successful (re)connect
        on_connect(client, None, None, 0)
    subscribed_topics = {c.args[0] for c in client.subscribe.call_args_list}
    assert subscribed_topics == {
        "home/A/pool/ble-yc01",
        "home/A/pool/pump",
    }


def test_on_connect_with_failure_does_not_resubscribe():
    mqtt.clear_subscriptions()
    mqtt.subscribe("home/A/pool/ble-yc01", lambda t, p: None)
    client = _make_client_mock()
    on_connect = mqtt._make_on_connect()
    on_connect(client, None, None, 5)  # rc != 0
    client.subscribe.assert_not_called()


def test_on_message_dispatches_to_callback():
    mqtt.clear_subscriptions()
    received = []
    mqtt.subscribe("home/H32/pool/ble-yc01", lambda topic, payload: received.append((topic, payload)))
    msg = MagicMock()
    msg.topic = "home/H32/pool/ble-yc01"
    msg.payload = json.dumps({"temp": 24.5, "pH": 7.2, "cl": 0.7}).encode("utf-8")
    mqtt._on_message(None, None, msg)
    assert received == [("home/H32/pool/ble-yc01", {"temp": 24.5, "pH": 7.2, "cl": 0.7})]


def test_on_message_malformed_json_dropped():
    mqtt.clear_subscriptions()
    received = []
    mqtt.subscribe("home/H32/pool/ble-yc01", lambda topic, payload: received.append(payload))
    msg = MagicMock()
    msg.topic = "home/H32/pool/ble-yc01"
    msg.payload = b"not-json"
    mqtt._on_message(None, None, msg)
    assert received == []


def test_on_message_non_object_payload_dropped():
    mqtt.clear_subscriptions()
    received = []
    mqtt.subscribe("home/H32/pool/ble-yc01", lambda topic, payload: received.append(payload))
    msg = MagicMock()
    msg.topic = "home/H32/pool/ble-yc01"
    msg.payload = b"[1, 2, 3]"  # valid JSON, but not an object
    mqtt._on_message(None, None, msg)
    assert received == []


def test_on_message_subscriber_exception_does_not_propagate():
    mqtt.clear_subscriptions()
    def bad_cb(topic, payload):
        raise RuntimeError("boom")
    mqtt.subscribe("home/H32/pool/ble-yc01", bad_cb)
    msg = MagicMock()
    msg.topic = "home/H32/pool/ble-yc01"
    msg.payload = b'{"temp": 1.0}'
    # Should not raise — exception is logged
    mqtt._on_message(None, None, msg)


def test_on_message_routes_to_correct_topic_only():
    mqtt.clear_subscriptions()
    a_received = []
    b_received = []
    mqtt.subscribe("home/A/pool/ble-yc01", lambda t, p: a_received.append(p))
    mqtt.subscribe("home/B/pool/ble-yc01", lambda t, p: b_received.append(p))
    msg = MagicMock()
    msg.topic = "home/A/pool/ble-yc01"
    msg.payload = b'{"temp": 1.0}'
    mqtt._on_message(None, None, msg)
    assert a_received == [{"temp": 1.0}]
    assert b_received == []


def test_disconnect_does_not_raise_unbound_local_error():
    """Regression: disconnect() must declare ``global _client``, otherwise
    the ``_client = None`` assignment makes the earlier ``if _client:``
    reference an unbound local (UnboundLocalError)."""
    # Not connected → should be a no-op.
    mqtt.disconnect()
    # Simulate connected + disconnect without crash.
    client = MagicMock()
    client.is_connected.return_value = True
    mqtt._client = client
    mqtt.disconnect()
    assert mqtt._client is None
