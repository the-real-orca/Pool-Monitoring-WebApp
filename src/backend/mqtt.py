import json
import logging
import ssl
from typing import Callable

import paho.mqtt.client as mqtt_lib

ClientCallback = Callable[[str, dict], None]

_client: mqtt_lib.Client | None = None
# (topic, callback) pairs, re-subscribed on every (re)connect.
_subscriptions: list[tuple[str, ClientCallback]] = []


def _make_on_connect() -> Callable:
    def on_connect(c, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            logging.error("MQTT connection failed (rc=%s)", reason_code)
            return
        logging.info("MQTT connected; resubscribing to %d topic(s)", len(_subscriptions))
        for topic, _cb in _subscriptions:
            c.subscribe(topic, qos=0)

    return on_connect


def _topic_matches(pattern: str, topic: str) -> bool:
    """Match ``topic`` against a subscription ``pattern`` supporting ``+`` and ``#`` wildcards."""
    p_parts = pattern.split("/")
    t_parts = topic.split("/")
    p_len = len(p_parts)
    t_len = len(t_parts)
    i = 0
    while i < p_len:
        p = p_parts[i]
        if p == "#":
            return True
        if p == "+":
            if i >= t_len:
                return False
            i += 1
            continue
        if i >= t_len or p != t_parts[i]:
            return False
        i += 1
    return i == t_len


def _on_message(c, userdata, msg):
    """Decode JSON payloads and dispatch to subscribed callbacks.

    Malformed payloads (non-JSON, JSON of wrong type) are logged and dropped
    so that a single bad publisher cannot take down the whole consumer.

    Subscriptions may use MQTT wildcards (``+`` for a single level, ``#`` for
    the remainder of the topic). The first matching subscription's callback
    is invoked with the raw topic string and the decoded payload.
    """
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        logging.warning("MQTT message on %s: failed to decode JSON: %s", msg.topic, e)
        return
    if not isinstance(payload, dict):
        logging.warning("MQTT message on %s: payload is not a JSON object, dropping", msg.topic)
        return
    logging.debug("MQTT recv: topic=%s payload=%s", msg.topic, payload)
    for topic, cb in _subscriptions:
        if _topic_matches(topic, msg.topic):
            try:
                cb(msg.topic, payload)
            except Exception as e:
                logging.exception("MQTT subscriber for %s raised: %s", topic, e)


def connect(host: str, port: int, user: str, password: str, tls: bool = False) -> None:
    global _client
    _client = mqtt_lib.Client(mqtt_lib.CallbackAPIVersion.VERSION2)
    if user:
        _client.username_pw_set(user, password)
    if tls:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        _client.tls_set_context(ctx)
    _client.reconnect_delay_set(min_delay=1, max_delay=300)
    _client.on_connect = _make_on_connect()
    _client.on_disconnect = lambda c, u, d, rc, p: (
        logging.warning("MQTT disconnected (rc=%s), reconnecting...", rc)
    )
    _client.on_message = _on_message
    _client.connect_async(host, port)
    _client.loop_start()
    logging.info("MQTT connecting to %s:%s", host, port)


def subscribe(topic: str, on_message: ClientCallback) -> None:
    """Register a topic + callback pair. Survives reconnects (re-subscribed
    in the on_connect handler)."""
    _subscriptions.append((topic, on_message))
    if _client is not None and _client.is_connected():
        _client.subscribe(topic, qos=0)
    logging.info("MQTT subscribe registered for %s", topic)


def subscriptions() -> list[tuple[str, ClientCallback]]:
    """Return a copy of the current subscription list. Used by tests."""
    return list(_subscriptions)


def clear_subscriptions() -> None:
    """Remove all subscriptions. Used by tests."""
    _subscriptions.clear()


def publish(topic: str, payload: dict) -> bool:
    if not is_connected():
        return False
    result = _client.publish(topic, json.dumps(payload), qos=1)
    return result.rc == mqtt_lib.MQTT_ERR_SUCCESS


def disconnect() -> None:
    global _client
    if _client:
        _client.loop_stop()
        _client.disconnect()
    _client = None


def is_connected() -> bool:
    return _client is not None and _client.is_connected()
