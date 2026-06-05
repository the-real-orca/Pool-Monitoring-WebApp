# Pool Monitor PWA

Progressive Web App for pool water management: manual measurement entry (pH, chlorine,
temperature), real-time Live View of BLE sensor + pump state, and a 7-day trend chart
of historical aggregates. Python/FastAPI backend bridges everything to an MQTT broker.

## Features

- **Manual measurement entry** via smartphone PWA (pH, chlorine, temperature)
- **Live View** (default landing): real-time dashboard fed by MQTT sensor and pump
  topics, with main temperature card, 5-sample means for pH / Cl, pump status icons
  and a 7-day zoomable trend chart
- **Touch-optimized UI**: ± stepper buttons, value slider, and full touch support for
  the trend chart (one-finger pan, two-finger pinch-zoom, double-tap reset)
- **AI image analysis** (optional): photograph a test strip + reference scale, the
  backend forwards it to a multimodal AI service and prefills pH / Cl into the form
  (rate-limited per day, images persisted for traceability)
- **Chemistry updates** (`POST /api/chem`): log chemical additions per pool and
  publish to `<pool-topic>/chem` (DE → EN enum mapping, optional amount + unit)
- **Multi-pool** support: pool list served from the backend, selector in the form
- **Optional `mqtt2mail` report service**: subscribes to pool topics and emails
  periodic reports (configurable times, multi-topic, fallback mail to stdout)
- **Bearer token authentication**, CORS locked to the production frontend URL
- **PWA** with offline-capable service worker (Workbox)
- **HTTPS production-ready** via Caddy + Let's Encrypt

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vue.js 3 (Composition API, JS), Tailwind CSS v4, Vite, uPlot |
| Backend | Python 3.12 FastAPI, paho-mqtt, OpenRouter SDK, SQLite (WAL) |
| Infrastructure | Docker Compose, Caddy (HTTPS), Mosquitto, mqtt2mail |
| Testing | pytest (backend), vitest + @vue/test-utils (frontend) |
| Linting | Ruff (backend) |

## Quick Start (Development)

```bash
# Copy environment template
cp src/.env.example src/.env

# Start all services
cd src && docker compose up -d

# Access
# - Frontend: http://localhost:2080
# - API: http://localhost:2080/api/status
```

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `API_TOKEN` | Bearer token for API authentication |
| `MQTT_HOST` / `MQTT_PORT` | MQTT broker (default: `mosquitto:2883`) |
| `MQTT_USER` / `MQTT_PASS` | MQTT credentials (optional) |
| `MQTT_TLS` | Enable TLS for the broker (`1`/`true` forces TLS, `0`/`false` forces plain) |
| `POOL_LIST` | JSON array of pool names and MQTT topics |
| `FRONTEND_URL` | Production frontend URL for CORS (e.g. `https://pool.io10.org`) |
| `LIVE_TOPIC_BLE_TEMPLATE` | MQTT topic template for sensor data (default: `home/{pool}/pool/ble-yc01`) |
| `LIVE_TOPIC_PUMP_TEMPLATE` | MQTT topic template for pump state |
| `LIVE_DB_PATH` | SQLite file for hourly aggregates + pump events (default: `/data/history/data.db`) |
| `AI_API_KEY` / `AI_MODEL` / `AI_PROVIDER` | Optional image analysis; rate-limited via `AI_MAX_REQUESTS_PER_DAY` |
| `LOG_LEVEL` | Root log level (default `INFO`; set `DEBUG` for per-MQTT / per-DB / per-aggregator-tick logs) |
| `REPORT_TIMES` / `REPORT_INTERVAL_MINUTES` | mqtt2mail report cadence |
| `MAIL_TO` | Recipient(s) for mqtt2mail SMTP report |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Health check (no auth) |
| `/api/pools` | GET | List available pools (auth required) |
| `/api/measurements` | POST | Submit manual measurement (auth required) |
| `/api/chem` | POST | Log a chemistry update (auth required) |
| `/api/analyze-image` | POST | Multipart upload; returns extracted pH / Cl (auth required) |
| `/api/pools/live` | GET | Pools with at least one live sample (auth required) |
| `/api/live` | GET | Latest snapshot for a pool (auth required) |
| `/api/history` | GET | Hourly aggregates for a metric over N days (auth required, supports `before_ts` backfill) |
| `/api/pump-events` | GET | Pump state changes for a pool (auth required) |

## Testing

```bash
# Backend tests
cd src/backend && pytest -v

# Frontend tests
cd src/frontend && npm run test
```

## Project Structure

```
src/
├── backend/
│   ├── main.py          # FastAPI app, routes, models
│   ├── mqtt.py          # MQTT client (publish + subscribe)
│   ├── db.py            # SQLite layer (WAL, hourly aggregates, pump events)
│   ├── live_state.py    # In-memory 5-sample ring buffer + pump state
│   ├── aggregator.py    # Per-hour / per-window rollup background task
│   ├── ai.py            # OpenRouter SDK client + image analysis
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.vue              # View switcher (live / form / chemistry / settings)
│   │   ├── main.js
│   │   ├── validation.js
│   │   ├── components/
│   │   │   ├── LiveView.vue           # Real-time dashboard
│   │   │   ├── TrendChart.vue         # uPlot, 3 panels, mouse + touch gestures
│   │   │   ├── PumpStatusCard.vue
│   │   │   ├── MeasurementForm.vue
│   │   │   ├── ChemicalUpdateForm.vue
│   │   │   ├── ImageCaptureModal.vue
│   │   │   ├── ValueSliderInput.vue
│   │   │   └── SettingsPanel.vue
│   │   └── composables/
│   │       ├── useApi.js          # fetch wrapper (incl. live / history)
│   │       ├── useSettings.js
│   │       ├── useImage.js
│   │       ├── useToast.js
│   │       └── useLiveData.js
│   ├── vite.config.js
│   └── package.json
├── mosquitto/
│   └── config/mosquitto.conf
├── mqtt2mail/
│   └── app/mqtt2mail.py
├── docker-compose.yml
├── Caddyfile
├── deploy-prepare.sh
└── .env.example
```

## Deployment

### Prepare Deployment Package

Run the deployment preparation script to build the frontend and create a deployable package:

```bash
cd src
./deploy-prepare.sh
```

This script:
1. Creates `deploy/` directory
2. Copies infrastructure files (docker-compose.yml, Caddyfile)
3. Copies backend source files
4. Builds frontend (npm install + npm run build)
5. Copies production-ready frontend (dist, Dockerfile, nginx.conf)

### Deploy to Server

```bash
# Copy to vServer
scp -r deploy/ user@vserver:/opt/pool-monitoring

# On server
cd /opt/pool-monitoring
docker compose up --build -d
```

See `docs/plan.md` for detailed implementation phases. Production deployment uses Caddy with automatic HTTPS via Let's Encrypt.

## License

MIT
