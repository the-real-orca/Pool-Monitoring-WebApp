import json
import logging
import ssl

import paho.mqtt.client as mqtt_lib

_client: mqtt_lib.Client | None = None


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
    _client.on_connect = lambda c, u, d, rc, p: (
        logging.info("MQTT connected (rc=%s)", rc)
        if rc == 0
        else logging.error("MQTT connection failed (rc=%s)", rc)
    )
    _client.on_disconnect = lambda c, u, d, rc, p: (
        logging.warning("MQTT disconnected (rc=%s), reconnecting...", rc)
    )
    _client.connect_async(host, port)
    _client.loop_start()
    logging.info("MQTT connecting to %s:%s", host, port)


def publish(topic: str, payload: dict) -> bool:
    if not is_connected():
        return False
    result = _client.publish(topic, json.dumps(payload), qos=1)
    return result.rc == mqtt_lib.MQTT_ERR_SUCCESS


def disconnect() -> None:
    if _client:
        _client.loop_stop()
        _client.disconnect()


def is_connected() -> bool:
    return _client is not None and _client.is_connected()
