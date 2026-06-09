# Reference: Architecture Overview & API

## 1. System Architecture

```
[ PWA (Vue) ] --HTTPS--> [ Caddy ] --/api/*--> [ FastAPI backend ] --MQTT--> [ Mosquitto ]
                              |                        |  ^                        |
                              \--/ ----> [ frontend    |  | subscribe <base>/+     |
                                          nginx ]      |  |                        |
                                                       v  |                        |
                                            [ SQLite (WAL) live store ]            |
                                                                                   |
   [ ESP/Arduino sensors + pump ] --publish <base>/ble-yc01, <base>/pump---------->|
                                                                                   |
                                              [ mqtt2mail ] --subscribe <base>/+ --/--> SMTP email reports
```

- **Caddy** terminates TLS (Let's Encrypt for `pool.io10.org`), routes `/api/*`
  to `backend:8000`, everything else to `frontend:80`. Raises body limit to
  12 MB only for `/api/analyze-image`.
- **Backend** is the only writer to MQTT (publishes manual measurements +
  events) and the MQTT subscriber for live sensor/pump data, which it
  aggregates into SQLite.
- **Frontend** is a static PWA served by nginx; it talks only to `/api/*`.
- **mqtt2mail** independently subscribes to pool topics and sends periodic
  email reports. It never talks to the backend.

## 2. Request / Data Flows

1. **Manual measurement:** PWA form → `POST /api/measurements` → backend
   validates (`Measurement` model) → publishes JSON to `<base>/manual`.
2. **Event:** PWA event form → `POST /api/event` → `Event` model → publishes to
   `<base>/event`.
3. **AI image:** PWA captures/compresses photo → `POST /api/analyze-image`
   (multipart) → backend calls OpenRouter multimodal model → returns `{ph, cl,
   warnings, image, requestsRemainingToday}`; persists image+JSON for audit.
4. **Live data (inbound):** sensors/pump publish to `<base>/ble-yc01`,
   `<base>/pump`. Backend subscribes `<base>/+`, a single content-driven
   handler routes by payload keys: `temp/pH/cl` → ring buffer; `mainPump/
   solarPump` → pump state (+ DB event on change). An async aggregator writes
   per-window means to SQLite.
5. **Live data (outbound):** PWA polls `GET /api/live` every 30 s and
   `GET /api/history` per metric for the 7-day chart.

## 3. MQTT Topic Model (Phase 23 — base-topic)

- `POOL_LIST` = JSON array of `{"name": "...", "topic": "<base>"}`.
- `topic` is the **base** (e.g. `home/H32/pool`). The backend subscribes once
  per pool to `<base>/+` and dispatches by JSON content.
- **Fixed suffixes:**
  - `<base>/ble-yc01` — sensor snapshot (inbound) → `{time,name,sensorType,temp,pH,cl}`
  - `<base>/pump` — pump state (inbound) → `{time,mainPump,solarPump}`
  - `<base>/manual` — manual measurement (outbound, backend → MQTT)
  - `<base>/event` — operational event (outbound, backend → MQTT)
- **Pump field names are hard-coded constants:** `mainPump`, `solarPump`,
  `time`. No env override (the old `LIVE_PUMP_FIELD_*` were removed).
- **Reserved suffixes:** `manual`, `event`, `pump` — pool names may not equal
  these. Base-topic validation rejects wildcards, `$`, whitespace, leading/
  trailing `/`.
- Wildcard matching in `mqtt.py` supports `+` (one level) and `#` (rest).
- Sample inbound payload: `docs/msg-sample.json`.

## 4. HTTP API Contract

Base path `/api`. All endpoints except `/api/status` require
`Authorization: Bearer <API_TOKEN>` (constant-time compare). A **missing**
header yields **422** (FastAPI required header), a **wrong** token **401**.

| Method | Path | Auth | Success | Errors | Purpose |
|--------|------|------|---------|--------|---------|
| GET | `/api/pools` | yes | 200 | 401 | List configured pool names |
| POST | `/api/measurements` | yes | 201 | 422, 503 | Publish manual measurement to `<base>/manual` |
| POST | `/api/event` | yes | 201 | 422, 503 | Publish event to `<base>/event` |
| POST | `/api/analyze-image` | yes | 200 | 400, 422, 429, 502, 503 | AI extract pH/cl from a photo |
| GET | `/api/pools/live` | yes | 200 | 401 | Pools that have ≥1 live sample |
| GET | `/api/live?pool=` | yes | 200 | 401, 422 | Live snapshot (temp, pH, cl mean, pumps, stale) |
| GET | `/api/history?pool=&metric=&days=&before_ts=` | yes | 200 | 422 | Aggregated history; `metric∈{temp,pH,cl}`, `days 1..30`, optional `before_ts` backfill |
| GET | `/api/pump-events?pool=&days=` | yes | 200 | 422 | Pump state-change events |
| GET | `/api/status` | **no** | 200 | — | Health: status, mqttConnected, uptime, version, aiConfigured, imageAnalysisRequestsToday, liveDataConfigured |

- **503** on measurement/event = MQTT publish failed (broker down).
- **/api/analyze-image** error mapping: refusal/schema → 422, AI auth → 502,
  timeout/service → 503, daily limit → 429, bad MIME/oversize → 400.
- **Rate limiting:** per-IP sliding window (`API_RATE_LIMIT_REQUESTS`/
  `_WINDOW_SECONDS`, default 60/60s) on `/api/*`, **except** the read-heavy
  polling prefixes `/api/history`, `/api/pump-events`, `/api/live`.

## 5. Data Shapes (wire)

**Measurement → `<base>/manual`:**
`{time:int, name, sensorType:"manual", pH, cl, temp, status?, aiPH?, aiCL?, aiImage?, aiCorrected?}`

**Event → `<base>/event`:**
`{time:int, name, eventType, amount?, unit?, note?}`
(`ph_minus` is sent as `eventType:"ph"` with a **negative** amount.)

**Event types:** `chlorine, ph, flocculant, refill, backwash, winter`
(frontend splits `ph` into `ph_plus`/`ph_minus`).
**Event units:** `ml, g, kg, tabs, l, min`.

## Known Issues (architecture/API)
- `/api/status` is unauthenticated → information disclosure (version, MQTT
  state, counts). Acceptable as a health check but note it.
- 429 responses bypass CORS headers (rate-limit middleware sits outside CORS) →
  browsers see a generic network error.
- **README documents the OLD API** (`/api/chem`, `LIVE_TOPIC_*` templates) — do
  not trust it; this file reflects the real contract.

See `reference/backend.md` for implementation detail and line references.
