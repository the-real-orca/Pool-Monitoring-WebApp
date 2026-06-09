# Reference: Containerization & Infrastructure

Location: `src/` (compose, Caddyfile, env, Dockerfiles, mosquitto, deploy script).

## docker-compose.yml (`src/docker-compose.yml`)

| Service | Build/Image | Ports | Volumes | Limits | Notes |
|---------|-------------|-------|---------|--------|-------|
| `frontend` | `./frontend` | — | — | 0.25 cpu / 64M | served via Caddy |
| `backend` | `./backend` | — | `./data/ai`, `./data/history` | 0.5 / 128M | `env_file: .env`; `depends_on: mosquitto` **commented out** |
| `caddy` | `caddy:2-alpine` | 80, 443 | `./Caddyfile:ro`, `caddy_data` | 0.25 / 64M | depends_on frontend+backend |
| `mqtt2mail_pool` | `./mqtt2mail/` | — | — | 0.25 / 64M | `env_file: .env`, `TZ` |
| `mqtt-publisher` | `./dev/mqtt-publisher` | — | — | 0.1 / 32M | `profiles:["debug"]`, opt-in only |
| `mosquitto` | `eclipse-mosquitto:2` | **2883:2883** | `./mosquitto/config:ro` | 0.1 / 16M | dev/test broker |

- Single default network. Restart `unless-stopped` (publisher `no`).
- Volumes: named `caddy_data`; bind mounts `./data/ai`, `./data/history`
  (gitignored via `data/`).

## Caddyfile (`src/Caddyfile`)
- **Production block** `pool.io10.org { ... }`: security headers
  (`X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy`,
  `Content-Security-Policy default-src 'self'; script-src 'self'; style-src
  'self' 'unsafe-inline'`), `/api/analyze-image` (12MB body) → backend,
  `/api/*` → `backend:8000`, `handle` → `frontend:80`. Auto-HTTPS.
- **Dev block** `:80 { ... }`: same routing, **no security headers**.

## Mosquitto (`src/mosquitto/config/mosquitto.conf`)
```
listener 2883
allow_anonymous true
```
No persistence configured. **Only listens on 2883** (default 1883 NOT created).

## Dockerfiles (Phase 14/24 hardening)
- `backend/Dockerfile`: `python:3.12-alpine`, `pip install
  --break-system-packages`, non-root `appuser`, `mkdir -p /data/history` +
  chown, `CMD uvicorn main:app --host 0.0.0.0 --port 8000`. `.dockerignore`
  keeps only `*.py` + `requirements.txt`.
- `frontend/Dockerfile`: multi-stage `node:22-alpine` → `nginx:1.27-alpine`,
  non-root. `Dockerfile_production`: nginx-only, copies pre-built `dist/`.
- `mqtt2mail/Dockerfile`: `python:3.12-alpine`, `--break-system-packages`,
  `USER appuser`.
- `dev/mqtt-publisher/Dockerfile`: `python:3.12-alpine` + tini; **runs as root**.

## Env files
- **`src/.env.example`** — template (placeholders). Vars: General
  (`LOG_LEVEL`, `TZ`, `FRONTEND_URL`, `API_TOKEN`, `POOL_LIST`), MQTT
  (`MQTT_HOST/PORT/TLS/TLS_INSECURE/USER/PASS/KEEPALIVE`), AI (`AI_*`), mqtt2mail
  (`REPORT_TIMES`, `SMTP_*`, `MAIL_*`, `SEND_EMPTY_REPORT`), Live (`LIVE_*`).
- **`src/.env`** — local dev (real test token). **`src/.env_production`** —
  **REAL production secrets** (`API_TOKEN`, `MQTT_PASS`, `AI_API_KEY=sk-…`,
  `SMTP_PASSWORD`). Both gitignored (`src/.gitignore`).
- Tracked env files (git): only `*.env.example`. **No secrets in git.**

## deploy-prepare.sh
Wipes/recreates `../deploy`; copies compose, Caddyfile, `.gitignore`,
`.env_production` → `deploy/.env`; backend `.py`+Docker files; creates
`data/history/.gitkeep`; copies mqtt2mail; **builds frontend** (`npm install` +
`npm run build`) and copies `dist/`+`public/`+nginx+`Dockerfile_production`.
**Does NOT copy mosquitto config** (lines 41-42 commented out).

## devcontainer
`.devcontainer/devcontainer.json` — dev environment setup (Codespaces).

## `deploy/` directory
**Generated** by `deploy-prepare.sh`, **gitignored** (`/deploy` in root
`.gitignore`). Currently a **STALE** copy: `deploy/backend/main.py` still has
`APP_VERSION="1.0.0"`, `/chem`, `RESERVED_SUFFIXES=("manual","chem","pump")`.
Do not edit `deploy/` — regenerate it. Treat `src/` as the single source.

## Known Issues
1. **Mosquitto port mismatch (functional bug):** broker listens on **2883**,
   but `.env.example`/`.env` set `MQTT_PORT=1883`, and TSD §6 claims "1883
   matches the dev listener". Backend→`mosquitto:1883` would fail. Either set
   `MQTT_PORT=2883` for the bundled broker or add a 1883 listener.
2. **`.env.example` stale:** lines 6-9, 50 reference `<base>/chem` /
   "chemistry messages" (should be `/event`, Phase 25/27).
3. **Documented-but-unread env vars:** `MQTT_TLS_INSECURE`, `MQTT_KEEPALIVE`
   (backend never reads them).
4. **Deploy mosquitto gap:** copied `docker-compose.yml` references
   `./mosquitto/config` but `deploy-prepare.sh` doesn't copy it → mosquitto in
   the deploy package mounts an empty dir.
5. **`depends_on: mosquitto` commented out** for backend & mqtt2mail — startup
   ordering not enforced (relies on reconnect).
6. **Dev Caddy `:80` block lacks security headers** (acceptable for local).
7. **`src/.env.example` SMTP placeholder typo** `tesr@mail.com`.
8. **Real production secrets present on disk** in `src/.env_production` —
   rotate if ever exposed; never copy outside the deploy flow.

## Conventions
- `src/` is the source of truth; `deploy/` is build output (never hand-edit).
- Pin base image tags; run containers as non-root (publisher is the exception).
- New env var → add to `src/.env.example` AND read it in code; verify
  `docker compose config` is clean.
- Verify after infra changes: `docker compose config`, then
  `pytest`/`npm run test`.
