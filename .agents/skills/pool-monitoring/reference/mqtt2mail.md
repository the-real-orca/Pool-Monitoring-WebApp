# Reference: MQTT2Mail Service & Dev MQTT-Publisher

## Part A — mqtt2mail (`src/mqtt2mail/`)

Standalone Python service that subscribes to pool MQTT topics, aggregates
sensor readings in memory, and emails periodic German-language status reports.
Single file: `app/mqtt2mail.py` (~823 lines). **No tests** (known gap).

### Topic resolution (Phase 23 — POOL_LIST only)
- `parse_pool_topics()` reads `POOL_LIST` (JSON `[{name,topic}]`), normalizes
  each base (strips trailing `/`).
- `resolve_topics()` derives, per base: data `<base>/+`, alert `<base>/+/alert`,
  availability `[]` (always empty — dead branch). Returns a 3-tuple.
- The old priority chain (`MQTT_TOPICS`, `MQTT_TOPIC_BASE`,
  `MQTT_ALERT_TOPICS`, `MQTT_AVAILABILITY_TOPICS`) was removed from the code.

### MQTT
- `Client(VERSION2)`; random client-id suffix (`os.urandom(4).hex()`) unless
  `MQTT_CLIENT_ID` set; `reconnect_delay_set(30,300)`; `on_subscribe` checks
  granted QoS; TLS uses `CERT_NONE` (unverified — see Known Issues).
- `on_message` classifies by payload content via `add_data`/`add_availability`.

### Reporting
- `reporter_loop` (daemon thread): if `REPORT_TIMES` (CSV `HH:MM`) set, fires at
  fixed clock times (`next_report_delay`), else every
  `REPORT_INTERVAL_MINUTES` (15). Skips empty windows unless `SEND_EMPTY_REPORT`.
- Per report: `snapshot_and_reset()`, build plain + HTML body, send.
- Subject auto-generated: `Pool Status - {sensor_name} ({format_subject_date})`,
  e.g. `Pool Status - Pool H32 (So. 7.6. @ 10:00)`. No `MAIL_SUBJECT` env.
- `PoolAggregator`: per-metric last/min/max + `deque(maxlen=5)` rolling mean;
  battery mV→V conversion; German alert humanization ("zu hoch"/"zu niedrig").
- `build_email_body` (plain) + `build_email_body_html` (primary temp/pH/cl
  table + secondary muted table). Footer `Empfangene Messungen: N`.

### Email sending
- `send_email`: STARTTLS (default, **verified** TLS via
  `ssl.create_default_context()`) or SSL path. Raises if SMTP creds missing.
- On send failure in `reporter_loop` → `print_report_to_stdout` fallback.
- `send_test_email` on startup (includes host outbound IP); logs on failure.

### Env vars
`POOL_LIST`, `MQTT_HOST/PORT/CLIENT_ID/USER(NAME)/PASS(WORD)/TLS/KEEPALIVE`,
`REPORT_TIMES`, `REPORT_INTERVAL_MINUTES`, `SEND_EMPTY_REPORT`, `LOG_LEVEL`,
`SMTP_HOST/PORT/USERNAME/PASSWORD/STARTTLS`, `MAIL_FROM/TO`,
`BAT_VALUE_UNIT/BAT_DISPLAY_UNIT`, `TZ`. See `src/mqtt2mail/.env.example`.

### Known Issues
1. **Unverified MQTT TLS** (`:747-751`): `check_hostname=False`+`CERT_NONE`, no
   insecure opt-in. Dangerous — this is a production service.
2. **Zero tests** — highest-risk untested module (clock math, topic resolution,
   wildcard matcher, email builders, battery conversion). Add
   `src/mqtt2mail/tests/test_mqtt2mail.py`.
3. **Permanent debug `print`** of every topic+payload to stdout (`:770`),
   ignoring `LOG_LEVEL` — leaks all sensor data to logs.
4. **`<b>` tags in the text/plain body** → raw tags in plaintext clients.
5. **Dead code:** `parse_topic_csv`, all `availability_*` branches (always empty).
6. **Event payloads inflate `message_count`** (counted but metric-less, ignored).
7. **README stale:** `src/mqtt2mail/README.md:81-100` still documents removed
   `MQTT_TOPICS`/`MQTT_TOPIC_BASE` priority chain. `.env.example:24` says
   "chemistry" (should be "event", Phase 25).

## Part B — Dev MQTT-Publisher (`src/dev/mqtt-publisher/`)

Synthetic publisher for local testing. `publisher.py` (~245 lines).
Tests: `pytest -v` → **11/11**.

- Config: prefers `POOL_LIST` (JSON `[{name,topic}]`); legacy fallback `POOLS`
  (names → `home/{pool}`). Derives `POOLS: list` and `POOL_BASE_TOPICS: dict`.
- **Hard-coded suffixes** `BLE_TOPIC_SUFFIX="ble-yc01"`, `PUMP_TOPIC_SUFFIX="pump"`.
- Per tick per pool publishes `<base>/ble-yc01` (`temp/pH/cl` w/ drift+noise) and
  `<base>/pump` (`mainPump` toggles every `PUMP_TOGGLE_EVERY`).
- **No CLI** — env-only (`INTERVAL_SECONDS`, `RANDOM_SEED`, `LOG_LEVEL`, etc.).
- Run via compose: `docker compose --profile debug up mqtt-publisher`.
- TLS secure / insecure (explicit `MQTT_TLS_INSECURE`) paths; `reconnect_delay_set(1,30)`.

### Known Issues
1. **Plan/code mismatch:** plan Phase 23.5 claims a `--pool/--kind` CLI and a
   `POOL_BASE_TOPICS` env var — **neither exists** (env-only; dict derived from
   `POOL_LIST`). The plan is internally inconsistent (23.6.6 vs 23.5.1).
2. **Container runs as root** (no `USER`), unlike mqtt2mail/backend.
3. **`_drive_loop` test helper is dead + broken** (sets non-existent `stop_flag`).
4. No tests for `POOL_LIST` parsing / `sys.exit(1)` paths / unknown-pool `KeyError`.

## Conventions
- Both services publish/subscribe by **base topic + fixed suffix**; never
  hardcode full topics.
- mqtt2mail derives all subscriptions from `POOL_LIST` only.
- When adding email content, update both plain and HTML builders + the footer.
