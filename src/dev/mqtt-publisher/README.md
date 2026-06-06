# Debug MQTT Publisher

Synthetic data source for the Pool-Monitoring Live View. Publishes a BLE-shaped
sensor payload and a pump-state payload for every configured pool, every
`INTERVAL_SECONDS`.

Pool configuration uses the canonical `POOL_LIST` (recommended) — a JSON list of
`{name, topic}` pairs identical to the main app's configuration. A legacy
`POOLS` env var (JSON list of names) is still honoured as a fallback for the
quick-start demo, but new setups should prefer `POOL_LIST` because it lets you
control the MQTT base topic per pool.

## Quick start

```bash
# from src/
docker compose --profile debug up mqtt-publisher
```

The service is **not** started by `docker compose up` — you must opt in with
`--profile debug` so production stacks are not affected.

## Configuration

All settings are environment variables (the compose file wires sensible
defaults that mirror the main app's topic layout):

| Variable | Default | Purpose |
| --- | --- | --- |
| `MQTT_HOST` | `mosquitto` | broker host |
| `MQTT_PORT` | `1883` | broker port |
| `MQTT_USER` / `MQTT_PASS` | empty | optional auth |
| `MQTT_TLS` | `false` | enable TLS |
| `MQTT_TLS_INSECURE` | `false` | skip server cert verification (self-signed brokers, debug only) |
| `POOL_LIST` | empty | **Primary.** JSON list of `{"name", "topic"}` pairs. The `topic` is the base topic (used for both `<base>/ble-yc01` and `<base>/pump`). |
| `POOLS` | `["Pool 1", "Pool 2"]` | **Legacy fallback.** JSON list of pool names. Each name is published with base topic `home/{pool}`. Only consulted when `POOL_LIST` is empty. |
| `INTERVAL_SECONDS` | `5` | publish period |
| `PUMP_TOGGLE_EVERY` | `12` | flip pump state every N ticks |
| `RANDOM_SEED` | empty | int seed for reproducible payloads |
| `LOG_LEVEL` | `INFO` | python log level |

> When `POOL_LIST` is set, it takes precedence. `POOLS` is only consulted when
> `POOL_LIST` is empty. The topic suffixes `ble-yc01` and `pump` are hard-coded
> in the publisher and are not configurable.

### Examples

Canonical form (recommended):

```bash
POOL_LIST='[{"name":"Pool 1","topic":"home/pool1"},{"name":"Pool 2","topic":"home/pool2"}]'
```

Legacy form (demo only):

```bash
POOLS='["Pool 1", "Pool 2"]'
# → topics: home/Pool 1/ble-yc01, home/Pool 1/pump, home/Pool 2/ble-yc01, home/Pool 2/pump
```

## Payloads

The published topics are `<base>/ble-yc01` and `<base>/pump`, where `<base>` is
the `topic` field from each `POOL_LIST` entry (or `home/{pool}` when the legacy
`POOLS` form is used).

**BLE** (`<base>/ble-yc01`):
```json
{
  "time": 1717500000,
  "name": "Pool 1",
  "sensorType": "ble-yc01",
  "temp": 24.6,
  "pH": 7.2,
  "cl": 0.71
}
```

**Pump** (`<base>/pump`):
```json
{
  "time": 1717500000,
  "mainPump": true,
  "solarPump": false
}
```

The `mainPump` cycle is `PUMP_TOGGLE_EVERY * INTERVAL_SECONDS` seconds (default
60 s on, 60 s off). `solarPump` runs for the first half of each cycle.

## Tests

```bash
cd src/dev/mqtt-publisher
python -m pytest tests/ -v
```
