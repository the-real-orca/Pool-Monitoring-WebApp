# Debug MQTT Publisher

Synthetic data source for the Pool-Monitoring Live View. Publishes a BLE-shaped
sensor payload and a pump-state payload for every configured pool, every
`INTERVAL_SECONDS`.

## Quick start

```bash
# from src/
docker compose --profile debug up mqtt-publisher
```

The service is **not** started by `docker compose up` — you must opt in with
`--profile debug` so production stacks are not affected.

## Configuration

All settings are environment variables (the compose file wires sensible
defaults that mirror the main `LIVE_TOPIC_*` templates):

| Variable | Default | Purpose |
| --- | --- | --- |
| `MQTT_HOST` | `mosquitto` | broker host |
| `MQTT_PORT` | `1883` | broker port |
| `MQTT_USER` / `MQTT_PASS` | empty | optional auth |
| `MQTT_TLS` | `false` | enable TLS |
| `MQTT_TLS_INSECURE` | `false` | skip server cert verification (self-signed brokers, debug only) |
| `POOLS` | `["Pool 1", "Pool 2"]` | JSON list of pool names |
| `BLE_TOPIC_TEMPLATE` | `home/{pool}/pool/ble-yc01` | sensor topic |
| `PUMP_TOPIC_TEMPLATE` | `home/{pool}/pool/pump` | pump topic |
| `INTERVAL_SECONDS` | `5` | publish period |
| `PUMP_TOGGLE_EVERY` | `12` | flip pump state every N ticks |
| `RANDOM_SEED` | empty | int seed for reproducible payloads |
| `LOG_LEVEL` | `INFO` | python log level |

## Payloads

**BLE** (`home/<pool>/pool/ble-yc01`):
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

**Pump** (`home/<pool>/pool/pump`):
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
