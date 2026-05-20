# Implementation Plan: Pool-Monitoring PWA

**Version:** 1.0 | **Based on:** TSD 1.0, FSD 1.0 | **Date:** 2026-05-17
**Legend:** `[ ]` open · `[x]` done

---

## Phase 1 – Project Structure & Configuration

Goal: empty but complete scaffold, all directories and root files present.

| # | File | Content |
|---|------|---------|
| [x] 1.1 | Create `src/` directory tree | `backend/`, `backend/tests/`, `frontend/src/components/`, `frontend/src/composables/`, `frontend/public/icons/`, `frontend/tests/` |
| [x] 1.2 | `src/.gitignore` | Python (`__pycache__/`, `.env`, `*.pyc`), Node (`node_modules/`, `dist/`), IDE (`.vscode/`, `.idea/`) |
| [x] 1.3 | `src/.env.example` | `API_TOKEN`, `MQTT_HOST`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASS`, `MQTT_TOPIC` |

**Verify:** `find src/ -type d` shows all expected directories. ✅


---

## Phase 2 – Infrastructure

Goal: all container and proxy configurations complete and syntactically correct.

| # | File | Content |
|---|------|---------|
| [x] 2.1 | `src/docker-compose.yml` | Services `frontend`, `backend`, `caddy`; volume `caddy_data`; `env_file: .env` for backend; `depends_on` |
| [x] 2.2 | `src/Caddyfile` | `handle /api/*` → `reverse_proxy backend:8000`; `handle` → `reverse_proxy frontend:80` |
| [x] 2.3 | `src/backend/Dockerfile` | `FROM python:3.12-slim`; `pip install -r requirements.txt`; `CMD uvicorn main:app --host 0.0.0.0 --port 8000` |
| [x] 2.4 | `src/frontend/Dockerfile` | Multi-stage: `node:22-alpine` build → `nginx:alpine` serve |
| [x] 2.5 | `src/frontend/nginx.conf` | SPA routing `try_files $uri /index.html`; static assets `expires 1y; Cache-Control immutable` |
| [x] 2.6 | `src/mosquitto/config/mosquitto.conf` | `listener 2883` · `allow_anonymous true` |
| [x] 2.7 | `src/docker-compose.yml` | Mosquitto: folder bind mount `./mosquitto/config:/mosquitto/config:ro`, Port `2883:2883` |

**Verify:** `docker compose config` runs without errors. ✅ Mosquitto container starts, binds port 2883, loads config from folder bind mount. ✅


---

## Phase 3 – Backend: Logic

Goal: fully functional backend, startable locally with `uvicorn`.

| # | File | Content |
|---|------|---------|
| [x] 3.1 | `backend/requirements.txt` | `fastapi>=0.115`, `uvicorn[standard]>=0.30`, `paho-mqtt>=2.0`, `python-dotenv>=1.0` |
| [x] 3.2 | `backend/pyproject.toml` | Ruff: `line-length=100`, `select=["E","F","I"]`; Black-compatible format |
| [x] 3.3 | `backend/mqtt.py` | `connect(host, port, user, password)` · `publish(topic, payload) → bool` · `disconnect()` · `is_connected() → bool`; paho `loop_start()` + `reconnect_delay_set(min=1, max=300)` |
| [x] 3.4 | `backend/main.py` | Config block `os.getenv` (6 lines) · `Measurement` Pydantic model (field boundaries, `name_alphanumeric`, `one_decimal`) · `build_mqtt_payload()` · `verify_token()` with `secrets.compare_digest` · `CORSMiddleware` · FastAPI lifespan (MQTT connect/disconnect) · `POST /api/measurements` (201/400/401/503) · `GET /api/status` |

**Verify:** `uvicorn main:app` starts. `GET /api/status` → `200 {"status":"healthy",...}`.


---

## Phase 4 – Backend: Tests

Goal: all critical paths covered by automated tests, `pytest` green.

| # | File | Test cases |
|---|------|------------|
| [x] 4.1 | `backend/tests/conftest.py` | `client` fixture: `TestClient` with `unittest.mock.patch` on `mqtt.publish` + `mqtt.is_connected` |
| [x] 4.2 | `backend/tests/test_models.py` | Valid measurement · exact boundaries (min/max per field) · overflow → `ValidationError` · rounding to 1 decimal · `name`: too short, too long, special chars → error |
| [x] 4.3 | `backend/tests/test_api.py` | `POST` 201 (valid) · 400 (invalid body) · 503 (MQTT down: `publish` returns `False`) · `GET /api/status` 200 with keys `status`, `mqttConnected`, `uptime`, `version` |
| [x] 4.4 | `backend/tests/test_auth.py` | Correct token → 201 · Wrong token → 401 · Missing header → 422 |

**Verify:** `pytest -v` → all tests green, 0 warnings.


---

## Phase 5 – Frontend: Base & Build Setup

Goal: empty Vue project builds through, Tailwind classes apply, PWA manifest is generated.

| # | File | Content |
|---|------|---------|
| [x] 5.1 | `frontend/package.json` | `vue@^3.5` · devDeps: `vite@^6`, `@vitejs/plugin-vue@^5`, `tailwindcss@^4`, `@tailwindcss/vite@^4`, `vite-plugin-pwa@^0.21`, `vitest@^2`, `@vue/test-utils@^2` · Scripts: `dev`, `build`, `test` |
| [x] 5.2 | `frontend/vite.config.js` | Plugins `vue()`, `tailwindcss()`, `VitePWA({registerType:'autoUpdate', manifest:{...}, workbox:{globPatterns:[...]}})` |
| [x] 5.3 | `frontend/index.html` | HTML shell, `<div id="app">`, viewport meta `width=device-width,initial-scale=1` |
| [x] 5.4 | `frontend/src/main.js` | `import './main.css'` · `createApp(App).mount('#app')` |
| [x] 5.5 | `frontend/src/main.css` | `@import "tailwindcss"` · `@theme` block: `--color-primary:#0EA5E9`, `--color-success:#22C55E`, `--color-warning:#F59E0B`, `--color-error:#EF4444` |
| [x] 5.6 | `frontend/public/icons/` | `icon-192.png`, `icon-512.png` (placeholder: sky blue with pool symbol) |

**Verify:** `npm run build` → `dist/` contains `manifest.webmanifest` and `sw.js`. ✅


---

## Phase 6 – Frontend: Logic (Composables & Constants)

Goal: all reusable logic blocks are isolated and independently testable.

| # | File | Content |
|---|------|---------|
| [x] 6.1 | `src/validation.js` | `FIELD_CONFIG`: `temp`, `pH`, `cl` each with `{ min, max, step, default, decimals, unit }` · `NAME_CONFIG`: `{ minLength:1, maxLength:50, pattern:/^[a-zA-Z0-9 ]+$/ }` |
| [x] 6.2 | `src/composables/useSettings.js` | Module-level `reactive(load())` · `watch(settings, save, {deep:true})` · token `btoa`/`atob` · `export function useSettings() { return { settings } }` |
| [x] 6.3 | `src/composables/useApi.js` | `postMeasurement(form)`: build payload (Unix timestamp, fixed fields) · `fetch` with `Authorization: Bearer` · differentiate 401 / 5xx / network error · returns `{ loading, error, postMeasurement }` |
| [x] 6.4 | `src/composables/useToast.js` | Module-level `reactive` toast state (`message`, `type`, `visible`) · `show(message, type='success', duration=3000)` with `clearTimeout` + auto-hide |

**Verify:** `npm run dev` starts (no import errors). ✅


---

## Phase 7 – Frontend: Components

Goal: all three UI components are complete, visually correct, touch-optimized.

| # | File | Content |
|---|------|---------|
| [x] 7.1 | `src/components/StepperInput.vue` | Props: `modelValue`, `min`, `max`, `step`, `decimals`, `unit` · `step(dir)`: `parseFloat(...toFixed(decimals))` + range check · emit `update:modelValue` · buttons ≥ 44×44px · `:disabled` at boundaries |
| [x] 7.2 | `src/components/MeasurementForm.vue` | `reactive` form state (defaults from `FIELD_CONFIG`, name from `settings.poolName`) · `datetime-local` → Unix timestamp on submit · `StepperInput` for temp/pH/cl · inline error messages · `submit()`: `postMeasurement` → toast + `resetForm()` or error display with retry · loading state on submit button · emit `open-settings` |
| [x] 7.3 | `src/components/SettingsPanel.vue` | `v-model` directly on `settings` · fields: token (password), pool name (text) · emit `close` · visible version string (from constant) |

**Verify:** `npm run dev` → form fully operable, settings open/close, stepper ± buttons respond correctly. ✅


---

## Phase 8 – Frontend: App Shell

Goal: complete app runs in the browser, all parts work together.

| # | File | Content |
|---|------|---------|
| [x] 8.1 | `src/App.vue` | `const view = ref('form')` · `v-if/v-else` for `MeasurementForm` / `SettingsPanel` · toast overlay (`useToast`) with `<Transition name="toast">` · Tailwind base layout: centered block, `max-w-sm`, `min-h-svh`, background color `#F8FAFC` |

**Verify:** `npm run dev` → full flow: form → send → toast · gear → settings → X → back · on mobile: touch targets sufficiently large. ✅


---

## Phase 9 – Frontend: Tests

Goal: critical frontend logic covered by automated tests, `vitest` green.

| # | File | Test cases |
|---|------|------------|
| [x] 9.1 | `tests/validation.spec.js` | All `FIELD_CONFIG` values correct (min/max/step/default/unit) · `NAME_CONFIG.pattern` matches valid names · rejected: special chars, empty string, >50 chars |
| [x] 9.2 | `tests/useSettings.spec.js` | Defaults when localStorage empty · save + load roundtrip · token Base64 roundtrip (`btoa`/`atob`) · reactivity: change to `settings` is written to localStorage |
| [x] 9.3 | `tests/StepperInput.spec.js` | Click `+` emits `modelValue + step` · click `-` emits `modelValue - step` · no emit when `modelValue === max` (button disabled) · no emit when `modelValue === min` (button disabled) · `toFixed(decimals)` rounding correct |

**Verify:** `npm run test` → all tests green. ✅ 19/19 passed.


---

## Phase 10 – Integration Test

Goal: all services run together in Docker, end-to-end fully verified.

| # | Step | Expected result |
|---|------|-----------------|
| [x] 10.1 | Create `.env` from `.env.example` | Token set, MQTT connection data configured |
| [x] 10.2 | `docker compose build` | All 3 images built, 0 errors |
| [x] 10.3 | `docker compose up -d` | All 3 containers running |
| [x] 10.4 | `curl http://localhost:2080/api/status` | `200 {"status":"healthy","mqttConnected":...}` |
| [x] 10.5 | `curl -X POST http://localhost:2080/api/measurements` with token + JSON | `201 {"status":"success",...}` |
| [x] 10.6 | MQTT broker: check topic `/pool/manual` | Message in msg-sample.json format received |
| [x] 10.7 | Open `http://localhost:2080` in browser | PWA form loads, send works, toast appears |

---

## Phase 11 – Polish: Settings UX

Goal: settings page uses explicit "Cancel" / "Save" buttons instead of a single "✕" close button.

| # | File | Content |
|---|------|---------|
| [x] 11.1 | `SettingsPanel.vue` | Replace "✕" button with "Cancel" + "Save" buttons at bottom · Cancel: revert settings to last saved state, emit `close` · Save: toast confirmation, emit `close` |

**Verify:** Settings: cancel reverts unsaved changes, save persists + toast.


---

## Phase 12 – Security & Production Deployment

Goal: CORS locked down, HTTPS production-ready, deployed to `pool.io10.org`.

| # | File | Content |
|---|------|---------|
| [x] 12.1 | `.env.example` | Add `FRONTEND_URL=https://pool.io10.org` |
| [x] 12.2 | `backend/main.py` | CORS: `allow_origins` reads `FRONTEND_URL` env var, no `*` fallback · log warning if `FRONTEND_URL` is empty |
| [x] 12.3 | `Caddyfile` | Production: `pool.io10.org { … }` with automatic HTTPS (Let's Encrypt) · Dev: keep `:80` for local testing |
| [x] 12.4 | `docker-compose.yml` | Add `FRONTEND_URL` env var to backend service |
| [x] 12.5 | `backend/mqtt.py` | TLS support for external MQTT with self-signed certificates (ssl.create_default_context) |
| [x] 12.6 | `backend/main.py` | `MQTT_TLS` env var: default based on port (8883), can be overridden |
| [ ] 12.7 | `Caddyfile` / `docker-compose.yml` | HTTPS test: `curl https://pool.io10.org/api/status` → 200 with valid cert |

**Verify:** CORS: wrong origin → blocked · HTTPS: Caddy serves with valid Let's Encrypt cert for `pool.io10.org`.


---

## Phase 13 – Deployment Prep

Goal: deployment package ready for vServer.

| # | File | Content |
|---|------|---------|
| [x] 13.1 | `deploy-prepare.sh` | Script copies all necessary files to `deployment/` directory |
| [x] 13.2 | `frontend/Dockerfile` | Simplified: uses pre-built `dist/` instead of building on server |
| [x] 13.3 | `.gitignore` | Updated for deployment |
| [x] 13.4 | `src/.gitignore` | Added Python caches, node_modules, dist |

**Verify:** `deployment/` contains all needed files, no `node_modules` or `src` folders.


---

## Phase 14 – Security Fixes

Goal: Alle identifizierten Security Issues behoben.

| # | Issue | File | Fix |
|---|-------|------|-----|
| [x] 14.1 | Docker Root User → non-root | `src/backend/Dockerfile` | `USER appuser` |
| [x] 14.2 | Docker Root User → non-root | `src/frontend/Dockerfile` | `USER appuser`, nginx cache dirs |
| [x] 14.3 | Rate Limiting | `src/backend/main.py` | Eigenes Middleware: 20 req/60s auf `/api/*` |
| [x] 14.4 | Rate Limiter IP detection | `src/backend/main.py` | `X-Forwarded-For` header support |
| [x] 14.5 | CORS einschränken | `src/backend/main.py` | `allow_methods=["POST","GET"]`, `allow_headers=["Authorization","Content-Type"]` |
| [x] 14.6 | Security Header | `src/Caddyfile` | CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy |
| [x] 14.7 | Base Image taggen | `src/backend/Dockerfile` | `FROM python:3.12.13-slim` |
| [x] 14.8 | Exposed credentials | `src/.gitignore` | `.env_production` ignoriert, Credentials rotiert |
| [x] 14.9 | Deploy script | `src/deploy-prepare.sh` | Frontend build, .gitignore kopieren |

**Verify:** `pytest -v` → all tests green. ✅


---

## Phase 15 – Feature: Pool List & Notes

Goal: Implement pool selection from backend list and optional notes field.

| # | File | Content |
|---|------|---------|
| [ ] 15.1 | `backend/main.py` | Add `POOL_LIST` parsing from env, `GET /api/pools`, update `POST /api/measurements` |
| [ ] 15.2 | `backend/models` | Update `Measurement` schema: `name` validator, add optional `notes` field |
| [ ] 15.3 | `frontend/useApi.js` | Add `fetchPools()` function |
| [ ] 15.4 | `frontend/MeasurementForm.vue`| Update UI to include pool select dropdown and notes textarea |
| [ ] 15.5 | `frontend/SettingsPanel.vue` | Remove `poolName` setting |
| [ ] 15.6 | Tests | Update and run all tests for frontend and backend |

**Verify:** `npm run test` and `pytest -v`




---


## File Overview

```
src/                                   27 files total
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Caddyfile
├── backend/                           9 files
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── main.py
│   ├── mqtt.py
│   └── tests/
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_api.py
│       └── test_auth.py
└── frontend/                          18 files
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── public/icons/
    │   ├── icon-192.png
    │   └── icon-512.png
    ├── src/
    │   ├── main.js
    │   ├── main.css
    │   ├── App.vue
    │   ├── validation.js
    │   ├── components/
    │   │   ├── StepperInput.vue
    │   │   ├── MeasurementForm.vue
    │   │   └── SettingsPanel.vue
    │   └── composables/
    │       ├── useSettings.js
    │       ├── useApi.js
    │       └── useToast.js
    └── tests/
        ├── validation.spec.js
        ├── useSettings.spec.js
        └── StepperInput.spec.js
```
