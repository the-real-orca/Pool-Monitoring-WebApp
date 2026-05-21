# Pool Monitor PWA

Progressive Web App for manual pool measurement entry (pH, chlorine, temperature) with Python/FastAPI backend bridge to MQTT broker.

## Features

- Manual measurement entry via smartphone PWA
- Touch-optimized UI with +/- stepper buttons
- Data transmission via REST API to MQTT broker
- Bearer token authentication
- PWA with offline support (service worker)
- Pool selection from backend-defined list

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vue.js 3 (Composition API), Tailwind CSS v4, Vite |
| Backend | Python FastAPI, paho-mqtt |
| Infrastructure | Docker Compose, Caddy (HTTPS), Mosquitto |
| Testing | pytest (backend), vitest (frontend) |

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
| `MQTT_HOST` | MQTT broker hostname (default: mosquitto) |
| `MQTT_PORT` | MQTT broker port (default: 2883) |
| `MQTT_USER` | MQTT username (optional) |
| `MQTT_PASS` | MQTT password (optional) |
| `POOL_LIST` | JSON array of pool names and MQTT topics |
| `FRONTEND_URL` | Production frontend URL for CORS |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Health check (no auth required) |
| `/api/pools` | GET | List available pools (auth required) |
| `/api/measurements` | POST | Submit measurement (auth required) |

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
│   ├── mqtt.py          # MQTT client
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── validation.js
│   │   ├── components/
│   │   └── composables/
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml
├── Caddyfile
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
