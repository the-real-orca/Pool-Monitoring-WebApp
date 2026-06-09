# Reference: Backend (FastAPI)

Location: `src/backend/`. Python 3.12, FastAPI, Pydantic v2, paho-mqtt 2.x.
Run tests: `cd src/backend && pytest -v` (**185 tests**). Lint: `ruff check .`
(line-length 100, rules `E,F,I`).

## Files

| File | Lines | Responsibility |
|------|-------|----------------|
| `main.py` | ~621 | Env config, models, middleware, all routes, MQTT dispatch, lifespan |
| `mqtt.py` | ~132 | paho client: connect/publish/subscribe/disconnect, wildcard match, TLS |
| `ai.py` | ~222 | OpenRouter image analysis, error classes, image persistence |
| `db.py` | ~216 | SQLite (WAL) schema + CRUD for aggregates & pump events |
| `live_state.py` | ~155 | Thread-safe in-memory ring buffers + pump state |
| `aggregator.py` | ~179 | Async background task: window rollup + daily cleanup |

## main.py structure

- **Env (read at import):** `LOG_LEVEL`, `API_TOKEN`, `API_RATE_LIMIT_REQUESTS`
  (60), `API_RATE_LIMIT_WINDOW_SECONDS` (60), `MQTT_HOST/PORT/USER/PASS`,
  `POOL_LIST` (→ `POOL_NAMES` set), `FRONTEND_URL`, `MQTT_TLS` (auto-true on
  port 8883), AI vars, `LIVE_*` vars. `APP_VERSION = "2.0"`.
- **Lifespan:** `db.init_db(LIVE_DB_PATH)` → build `LiveState` → build
  `Aggregator` → build `_base_to_pool_map` from `POOL_LIST` (validating each
  entry, skipping invalid ones) → subscribe `<base>/+` per pool →
  `mqtt.connect()` → `ai.startup()` → `aggregator.start()`. Reverse on shutdown.
- **Middleware:** `CORSMiddleware` (origins=[FRONTEND_URL], methods POST/GET,
  headers Authorization/Content-Type) + custom `RateLimitMiddleware` (per-IP,
  `threading.Lock`, exempts `/api/history`, `/api/pump-events`, `/api/live`).
- **Auth:** `verify_token` uses `secrets.compare_digest("Bearer "+API_TOKEN)`.
- **MQTT dispatch:** `_handle_pool_message` resolves pool by base prefix
  (`_resolve_pool_for_topic`), then routes by payload keys — `temp/pH/cl` →
  `live_state.push_sample`; `mainPump/solarPump` → `live_state.set_pump`
  (+ `db.insert_pump_event` on change, throttled by
  `_should_persist_pump_event`); other (e.g. event) payloads ignored.
  `_strict_bool` rejects truthy strings like `"false"`.

## Pydantic models

- **`Measurement`**: `time:int`, `name(1-50, must be in POOL_NAMES)`,
  `sensorType="manual"`, `pH(0-14)`, `cl(0-10)`, `temp(5-45)`,
  `status?(≤100)`, `aiPH?/aiCL?:float`, `aiImage?(≤200)`, `aiCorrected?:bool`.
  Validators: `valid_pool_name`, `one_decimal` (rounds pH/cl/temp).
- **`EventType`** enum: `chlorine, ph, flocculant, refill, backwash, winter`.
- **`EventUnit`** enum: `ml, g, kg, tabs, l, min`.
- **`Event`**: `time`, `name`, `eventType`, `amount?:float`, `unit?:EventUnit`,
  `note?(≤500)`. `validate_amount_unit_pair` (both or neither); no amount range
  (negative allowed for ph-minus).
- **`ImageAnalysisResult`** (`ai.py`): `ph, cl, refusal?, warnings?, image?`.
- **Payload builders:** `build_mqtt_payload` → `<base>/manual`;
  `build_event_payload` → `<base>/event`.

## mqtt.py
- `connect()` creates `Client(CallbackAPIVersion.VERSION2)`, sets auth, TLS,
  `reconnect_delay_set(1,300)`, `connect_async` + `loop_start`.
- `_make_on_connect` re-subscribes all registered subscriptions on reconnect.
- `_topic_matches` implements `+`/`#` semantics. `_on_message` JSON-decodes,
  drops non-dict, dispatches to **all** matching handlers.
- `publish()` returns False if disconnected; QoS 1; returns on PUBLISH enqueue
  (not PUBACK). `disconnect()` stops the loop.

## ai.py
- Lazily creates `openrouter.OpenRouter(api_key=...)` in `startup()` only if
  `AI_API_KEY` set; prunes old images on startup.
- `analyze_pool_image(image_bytes, mime)`: base64 data-URI → chat request with
  JSON-schema `response_format` from `ImageAnalysisResult` → maps SDK
  exceptions to `AIAuthError`/`AITimeoutError`/`AIServiceError`; checks
  refusal/empty/schema; `_normalize_keys` alias map (`pH/Cl/chlorine` →
  `ph`/`cl`); persists `<storage>/<date>/<ts>_<sha12>.{jpg,json}`.
- Daily rate limit lives in **main.py** (`ai_rate_check_and_increment`, UTC bucket).

## Live-data layer
- **db.py:** single connection, autocommit, `journal_mode=WAL`,
  `synchronous=NORMAL`. Tables: `measurements(pool,metric,timewindow_start,
  value,sample_count, PK)`, `pump_events(id,pool,pump,state,time,received_at)`.
  Module `_lock` serializes writes. Functions: `insert_aggregate` (INSERT OR
  REPLACE), `insert_pump_event`, `get_aggregates`, `get_aggregates_range`,
  `get_pump_events`, `cleanup_old_rows`.
- **live_state.py:** per-metric `deque(maxlen=ring_size)` (default 5), pump
  state `{state, since}`; `get_snapshot` returns mean-of-ring + `stale`/
  `staleSeconds`; single `Lock`. Metrics `temp/pH/cl`, pumps `main/solar`.
- **aggregator.py:** async loop ticks every `tick_seconds` (30), flushes the
  previous completed window's mean per (pool,metric); daily cleanup at
  `cleanup_hour_utc` gated by `min_cleanup_interval`. Never raises (failures
  logged).

## Tests (185)

`test_api.py` (29), `test_models.py` (42), `test_auth.py` (3),
`test_mqtt.py` (15), `test_handlers.py` (29), `test_db.py` (11),
`test_live_state.py` (17), `test_aggregator.py` (11), `test_api_live.py` (17).
`conftest.py` patches mqtt/db/aggregator, sets `API_TOKEN=test-token`, provides
temp DB + `mock_analyze_image`.

## Known Issues (fix carefully; tests are green despite these)

1. **MQTT TLS verification disabled** (`mqtt.py:83-84`): `check_hostname=False`,
   `CERT_NONE` set unconditionally when `tls=True`. `MQTT_TLS_INSECURE` is
   documented but never read → always insecure (MITM risk).
2. **Rate-limiter memory leak** (`main.py:281-285`): the empty-bucket cleanup
   never fires; per-IP buckets grow unbounded.
3. **Pump throttle keyed by pool, not (pool,pump)** (`main.py:202-204`): a
   simultaneous second-pump change is dropped from `pump_events`.
4. **Dead code:** `defaultdict` import, `PUMP_FIELDS`, `RESERVED_SUFFIXES`
   (defined, unused), `_base_to_pool()` (uncalled), duplicate `FRONTEND_URL`
   read (`:52` & `:59`), `AI_MAX_IMAGE_BYTES` duplicated in `ai.py`,
   `Iterable` import in `db.py`.
5. **`python-dotenv` in requirements.txt but never imported** (env via compose).
6. **`AI_IMAGE_RETENTION_DAYS`** default `30` (code) vs `.env.example` `60`.
7. **Aggregator** drops the in-progress window on shutdown; ring size 5 can lose
   samples under high publish rates.
8. **Test smells:** `test_api_live.py:19` patches non-existent
   `_topic_to_pool_map`; `test_api.py` passes a non-existent `time=` to
   `ImageAnalysisResult`.

## Conventions
- New env vars: read via `os.getenv` in the top config block of `main.py` with a
  safe default; document in `src/.env.example`.
- New endpoints: add `Depends(verify_token)` (except health), validate
  `pool` against `POOL_NAMES`, return precise status codes, add tests.
- Keep `mqtt.publish` API stable. Never raise from MQTT callbacks or the
  aggregator loop.
