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
* ``POOL_LIST``               JSON list of ``{"name","topic"}`` pairs; the
                              ``topic`` is the base topic (used for both
                              ``<base>/ble-yc01`` and ``<base>/pump``)
* ``POOLS``                   *legacy* JSON list of pool names (used only
                              when ``POOL_LIST`` is not set)
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

# Pool/base-topic configuration. Prefer the canonical ``POOL_LIST`` (same
# format as the main app); fall back to a legacy ``POOLS`` list of names
# with a hard-coded default base topic for the demo.
_default_pool_list = (
    '[{"name": "Pool 1", "topic": "home/pool1"},'
    ' {"name": "Pool 2", "topic": "home/pool2"}]'
)
_raw_pool_list = os.getenv("POOL_LIST", "").strip()
_pools: list[dict[str, str]] = []
if _raw_pool_list:
    try:
        parsed = json.loads(_raw_pool_list)
    except json.JSONDecodeError as e:
        log.error("POOL_LIST env var is not valid JSON: %s (%r)", e, _raw_pool_list)
        sys.exit(1)
    if not isinstance(parsed, list) or not all(
        isinstance(p, dict) and isinstance(p.get("name"), str) and isinstance(p.get("topic"), str)
        for p in parsed
    ):
        log.error("POOL_LIST must be a JSON array of {name, topic} objects: %r", parsed)
        sys.exit(1)
    _pools = [{"name": p["name"], "topic": p["topic"]} for p in parsed]
else:
    _raw_pools = os.getenv("POOLS", '["Pool 1", "Pool 2"]')
    try:
        names = json.loads(_raw_pools)
        if not isinstance(names, list) or not all(isinstance(p, str) for p in names):
            raise ValueError
    except (ValueError, json.JSONDecodeError):
        log.error("POOLS env var is not a JSON list of strings: %r", _raw_pools)
        sys.exit(1)
    _DEFAULT_BASE = "home/{pool}"
    for name in names:
        _pools.append({"name": name, "topic": _DEFAULT_BASE.format(pool=name)})

# Backwards-compatible list of pool names (used by tests / log lines).
POOLS: list[str] = [p["name"] for p in _pools]
# Per-pool base topic. Tests can monkey-patch this.
POOL_BASE_TOPICS: dict[str, str] = {p["name"]: p["topic"] for p in _pools}

# Default concrete topic suffixes (not configurable in the live stack).
BLE_TOPIC_SUFFIX = "ble-yc01"
PUMP_TOPIC_SUFFIX = "pump"

_seed_raw = os.getenv("RANDOM_SEED", "").strip()
if _seed_raw:
    rng = random.Random(int(_seed_raw))
else:
    rng = random.Random()


# --- payload generation ----------------------------------------------------


def _ble_topic(pool: str) -> str:
    base = POOL_BASE_TOPICS.get(pool)
    if not base:
        raise KeyError(f"No base topic configured for pool {pool!r}")
    return f"{base}/{BLE_TOPIC_SUFFIX}"


def _pump_topic(pool: str) -> str:
    base = POOL_BASE_TOPICS.get(pool)
    if not base:
        raise KeyError(f"No base topic configured for pool {pool!r}")
    return f"{base}/{PUMP_TOPIC_SUFFIX}"


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
    return _ble_topic(pool), payload


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
    return _pump_topic(pool), payload


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
