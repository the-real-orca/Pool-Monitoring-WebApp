"""Debug MQTT publisher for the Pool-Monitoring stack.

Publishes synthetic sensor and pump-state payloads at a fixed interval so
the Live View can be exercised without a real BLE / pump device.

Configuration via environment variables:

* ``MQTT_HOST``               broker hostname (default: ``mosquitto``)
* ``MQTT_PORT``               broker port (default: ``1883``)
* ``MQTT_USER`` / ``MQTT_PASS``  optional credentials
* ``MQTT_TLS``                ``true`` to enable TLS
* ``MQTT_TLS_INSECURE``       ``true`` to skip TLS certificate verification
                              (accepts self-signed certs — debug only)
* ``POOLS``                   JSON list of pool names
* ``BLE_TOPIC_TEMPLATE``      default: ``home/{pool}/pool/ble-yc01``
* ``PUMP_TOPIC_TEMPLATE``     default: ``home/{pool}/pool/pump``
* ``INTERVAL_SECONDS``        publish period (default: ``5``)
* ``PUMP_TOGGLE_EVERY``       flip pump state every N ticks (default: ``12``)
* ``RANDOM_SEED``             optional int seed for deterministic output
* ``LOG_LEVEL``               default: ``INFO``
"""
from __future__ import annotations

import json
import logging
import os
import random
import signal
import ssl
import sys
import time
from typing import Any

import paho.mqtt.client as mqtt_lib

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("mqtt-publisher")

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")
MQTT_TLS = os.getenv("MQTT_TLS", "false").lower() == "true"
# When MQTT_TLS=true, this skips server certificate verification. Useful
# for development brokers with self-signed certs. Never enable in
# production (MITM exposure).
MQTT_TLS_INSECURE = os.getenv("MQTT_TLS_INSECURE", "false").lower() == "true"

INTERVAL_SECONDS = max(1, int(os.getenv("INTERVAL_SECONDS", "5")))
PUMP_TOGGLE_EVERY = max(1, int(os.getenv("PUMP_TOGGLE_EVERY", "12")))

DEFAULT_BLE_TEMPLATE = "home/{pool}/pool/ble-yc01"
DEFAULT_PUMP_TEMPLATE = "home/{pool}/pool/pump"
BLE_TOPIC_TEMPLATE = os.getenv("BLE_TOPIC_TEMPLATE", DEFAULT_BLE_TEMPLATE)
PUMP_TOPIC_TEMPLATE = os.getenv("PUMP_TOPIC_TEMPLATE", DEFAULT_PUMP_TEMPLATE)

_raw_pools = os.getenv("POOLS", '["Pool 1", "Pool 2"]')
try:
    POOLS: list[str] = json.loads(_raw_pools)
    if not isinstance(POOLS, list) or not all(isinstance(p, str) for p in POOLS):
        raise ValueError
except ValueError:
    log.error("POOLS env var is not a JSON list of strings: %r", _raw_pools)
    sys.exit(1)

_seed_raw = os.getenv("RANDOM_SEED", "").strip()
if _seed_raw:
    rng = random.Random(int(_seed_raw))
else:
    rng = random.Random()


# --- payload generation ----------------------------------------------------


def _ble_payload(pool: str, tick: int) -> tuple[str, dict[str, Any]]:
    """Build a realistic BLE-YC01-shaped payload with slow drift + noise."""
    # Base values drift over time so the trend chart shows a visible curve.
    drift = (tick // 6) % 20
    temp = round(24.0 + drift * 0.05 + rng.uniform(-0.3, 0.3), 1)
    ph = round(7.2 + rng.uniform(-0.2, 0.2), 1)
    cl = round(max(0.1, 0.7 + rng.uniform(-0.2, 0.2)), 2)
    payload = {
        "time": int(time.time()),
        "name": pool,
        "sensorType": "ble-yc01",
        "temp": temp,
        "pH": ph,
        "cl": cl,
    }
    return BLE_TOPIC_TEMPLATE.format(pool=pool), payload


def _pump_payload(pool: str, tick: int) -> tuple[str, dict[str, Any]]:
    """Build a pump-state payload. State flips every PUMP_TOGGLE_EVERY ticks
    so the UI sees a visible ON/OFF cycle."""
    cycle = tick // PUMP_TOGGLE_EVERY
    main = (cycle % 2) == 0
    # Solar pump runs in the first half of each cycle and off in the second.
    solar = ((cycle * 2 + (tick // (PUMP_TOGGLE_EVERY // 2 or 1))) % 2) == 0
    payload = {
        "time": int(time.time()),
        "mainPump": bool(main),
        "solarPump": bool(solar),
    }
    return PUMP_TOPIC_TEMPLATE.format(pool=pool), payload


# --- mqtt plumbing ---------------------------------------------------------


def _build_client() -> mqtt_lib.Client:
    client = mqtt_lib.Client(mqtt_lib.CallbackAPIVersion.VERSION2,
                             client_id=f"mqtt-publisher-{os.getpid()}")
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    if MQTT_TLS:
        if MQTT_TLS_INSECURE:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            client.tls_set_context(ctx)
            log.warning("MQTT_TLS_INSECURE=true: server certificate is NOT verified (debug only)")
        else:
            client.tls_set()
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.enable_logger(log)
    return client


def _connect_with_retry(client: mqtt_lib.Client) -> None:
    delay = 1
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            log.info("MQTT publisher connected to %s:%d", MQTT_HOST, MQTT_PORT)
            return
        except OSError as e:
            log.warning("connect failed: %s — retrying in %ds", e, delay)
            time.sleep(delay)
            delay = min(delay * 2, 30)


# --- main loop -------------------------------------------------------------


def run(client: mqtt_lib.Client | None = None) -> int:
    """Run the publisher loop until SIGINT/SIGTERM. Returns process exit code."""
    if client is None:
        client = _build_client()
        _connect_with_retry(client)
        client.loop_start()

    stop = {"flag": False}

    def _handle_signal(signum, _frame):
        log.info("signal %d received, shutting down", signum)
        stop["flag"] = True

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    tick = 0
    try:
        while not stop["flag"]:
            for pool in POOLS:
                ble_topic, ble_payload = _ble_payload(pool, tick)
                pump_topic, pump_payload = _pump_payload(pool, tick)
                client.publish(ble_topic, json.dumps(ble_payload), qos=0)
                client.publish(pump_topic, json.dumps(pump_payload), qos=0)
                log.debug("published for %s: ble=%s pump=%s",
                          pool, ble_payload["temp"], pump_payload["mainPump"])
            tick += 1
            # Sleep in small chunks so SIGTERM is acted on quickly.
            slept = 0.0
            while slept < INTERVAL_SECONDS and not stop["flag"]:
                step = min(0.5, INTERVAL_SECONDS - slept)
                time.sleep(step)
                slept += step
    finally:
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:
            pass
    log.info("publisher stopped")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
