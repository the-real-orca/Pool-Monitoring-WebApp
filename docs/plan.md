# Implementation Plan: Pool-Monitoring PWA

**Version:** 1.0 | **Based on:** TSD 1.0, FSD 1.0 | **Date:** 2026-05-28
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
| [x] 2.1 | `src/docker-compose.yml` | Services `frontend`, `backend`, `caddy`, `mosquitto`, `mqtt2mail_pool`; volumes `caddy_data`, `ai_data`; `env_file: .env` for backend; `depends_on` |
| [x] 2.2 | `src/Caddyfile` | `handle /api/*` → `reverse_proxy backend:8000`; `handle` → `reverse_proxy frontend:80` |
| [x] 2.3 | `src/backend/Dockerfile` | `FROM python:3.12-slim`; `pip install -r requirements.txt`; `CMD uvicorn main:app --host 0.0.0.0 --port 8000` |
| [x] 2.4 | `src/frontend/Dockerfile`, `src/frontend/Dockerfile_production` | Dev: multi-stage `node:22-alpine` build → `nginx:alpine` serve; Production: uses pre-built `dist/` |
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
| [x] 3.3 | `backend/mqtt.py` | `connect(host, port, user, password, tls=False)` · `publish(topic, payload) → bool` · `disconnect()` · `is_connected() → bool`; paho `loop_start()` + `reconnect_delay_set(min=1, max=300)`; TLS with `check_hostname=False`, `CERT_NONE` for self-signed certs |
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
| [x] 6.3 | `src/composables/useApi.js` | `postMeasurement(form)`: build payload (Unix timestamp, fixed fields, AI traceability fields) · `fetchPools()`: fetch pool list from backend · `analyzeImage(file)`: POST image to AI endpoint · `fetch` with `Authorization: Bearer` · differentiate 401 / 5xx / network error · returns `{ loading, error, postMeasurement, fetchPools, analyzeImage }` |
| [x] 6.4 | `src/composables/useToast.js` | Module-level `reactive` toast state (`message`, `type`, `visible`) · `show(message, type='success', duration=3000)` with `clearTimeout` + auto-hide |

**Verify:** `npm run dev` starts (no import errors). ✅


---

## Phase 7 – Frontend: Components

Goal: all three UI components are complete, visually correct, touch-optimized.

| # | File | Content |
|---|------|---------|
| [x] 7.1 | `src/components/StepperInput.vue` | Props: `modelValue`, `min`, `max`, `step`, `decimals`, `unit` · `step(dir)`: `parseFloat(...toFixed(decimals))` + range check · emit `update:modelValue` · buttons ≥ 44×44px · `:disabled` at boundaries *(replaced by ValueSliderInput for temp/pH/cl)* |
| [x] 7.2 | `src/components/ValueSliderInput.vue` | Stepper + Popover-Slider combo: `[-] [Value] [+]` – clicking the value opens an overlay slider spanning full container width (bottom-sheet style) · internal integer range (0..N) mapped to decimal step · 5s idle timeout, 1s release timeout, click outside to close · holding +/- buttons starts repetition after 500ms (every 100ms) · `v-model` compatible |
| [x] 7.3 | `src/components/MeasurementForm.vue` | `reactive` form state (defaults from `FIELD_CONFIG`, name from `settings.poolName`) · `datetime-local` → Unix timestamp on submit · `ValueSliderInput` for temp/pH/cl · inline error messages · `submit()`: `postMeasurement` → toast + `resetForm()` or error display with retry · loading state on submit button · emit `open-settings` |
| [x] 7.4 | `src/components/SettingsPanel.vue` | `v-model` directly on `settings` · fields: token (password) · emit `close` · visible version string (from constant) |

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
| [x] 10.2 | `docker compose build` | All 5 images built, 0 errors |
| [x] 10.3 | `docker compose up -d` | All 5 containers running |
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
| [x] 12.5 | `backend/mqtt.py` | TLS support for external MQTT: `ssl.create_default_context()` with `check_hostname=False`, `verify_mode=CERT_NONE` for self-signed certificates |
| [x] 12.6 | `backend/main.py` | `MQTT_TLS` env var: default based on port (8883), can be overridden |
| [x] 12.7 | `Caddyfile` / `docker-compose.yml` | HTTPS test: `curl https://pool.io10.org/api/status` → 200 with valid cert |

**Verify:** CORS: wrong origin → blocked · HTTPS: Caddy serves with valid Let's Encrypt cert for `pool.io10.org`.


---

## Phase 13 – Deployment Prep

Goal: deployment package ready for vServer.

| # | File | Content |
|---|------|---------|
| [x] 13.1 | `deploy-prepare.sh` | Script copies all necessary files to `deployment/` directory |
| [x] 13.2 | `frontend/Dockerfile_production` | Production Dockerfile: uses pre-built `dist/` instead of building on server; copied as `Dockerfile` during deployment |
| [x] 13.3 | `.gitignore` | Updated for deployment |
| [x] 13.4 | `src/.gitignore` | Added Python caches, node_modules, dist |

**Verify:** `deployment/` contains all needed files, no `node_modules` or `src` folders.


---

## Phase 14 – Security Fixes

Goal: All identified security issues fixed.

| # | Issue | File | Fix |
|---|-------|------|-----|
| [x] 14.1 | Docker Root User → non-root | `src/backend/Dockerfile` | `USER appuser` |
| [x] 14.2 | Docker Root User → non-root | `src/frontend/Dockerfile` | `USER appuser`, nginx cache dirs |
| [x] 14.3 | Rate Limiting | `src/backend/main.py` | Custom middleware: 20 req/60s on `/api/*` |
| [x] 14.4 | Rate Limiter IP detection | `src/backend/main.py` | `X-Forwarded-For` header support |
| [x] 14.5 | Restrict CORS | `src/backend/main.py` | `allow_methods=["POST","GET"]`, `allow_headers=["Authorization","Content-Type"]` |
| [x] 14.6 | Security Header | `src/Caddyfile` | CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy |
| [x] 14.7 | Pin base image tag | `src/backend/Dockerfile` | `FROM python:3.12.13-slim` |
| [x] 14.8 | Exposed credentials | `src/.gitignore` | `.env_production` ignored, credentials rotated |
| [x] 14.9 | Deploy script | `src/deploy-prepare.sh` | Frontend build, copy .gitignore |

**Verify:** `pytest -v` → all tests green. ✅


---

## Phase 15 – Feature: Pool List & Notes

Goal: Implement pool selection from backend list and optional status field.

| # | File | Content |
|---|------|---------|
| [x] 15.1 | `backend/main.py` | Add `POOL_LIST` parsing from env, `GET /api/pools`, update `POST /api/measurements` |
| [x] 15.2 | `backend/models` | Update `Measurement` schema: `name` validator, add optional `status` field (max_length=100) |
| [x] 15.3 | `frontend/useApi.js` | Add `fetchPools()` function |
| [x] 15.4 | `frontend/MeasurementForm.vue`| Update UI to include pool select dropdown and status textarea |
| [x] 15.5 | `frontend/SettingsPanel.vue` | Remove `poolName` setting |
| [x] 15.6 | Tests | Update and run all tests for frontend and backend |

**Verify:** `npm run test` and `pytest -v` → all tests green. ✅


---

## Phase 16 – Feature: Automatic Image Analysis

Goal: User captures a photo of test strips + reference scale, the backend forwards
it to a multimodal AI service, extracts pH/chlorine and prefills the form.
Hardened with per-day rate limit, image persistence for debugging, and explicit
error mapping for refusals/timeouts/auth failures.

### 16.1 Backend – AI client & configuration

| # | File | Content |
|---|------|---------|
| [x] 16.1.1 | `src/.env.example` | Add `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`, `AI_MAX_REQUESTS_PER_DAY=10`, `AI_TIMEOUT_SECONDS=30`, `AI_IMAGE_STORAGE_PATH=/data/ai`, `AI_IMAGE_RETENTION_DAYS=30`, `AI_MAX_IMAGE_BYTES=10485760` |
| [x] 16.1.2 | `src/backend/requirements.txt` | Add `python-multipart>=0.0.9`, `openrouter>=0.9,<1.0`, `pytest-asyncio>=0.23` |
| [x] 16.1.3 | `src/backend/main.py` | Read AI env vars; `_ai_counter` UTC-day bucket; `ai_rate_check_and_increment()` |
| [x] 16.1.4 | `src/backend/ai.py` | `ImageAnalysisResult` Pydantic model (fields: `ph`, `cl`, `refusal`, `warnings`, `image`) · `analyze_pool_image(image_bytes, mime)` using official `openrouter` Python SDK · `response_format=ImageAnalysisResult` Pydantic → JSON schema · system prompt constant (includes -1 for unreliable pads, interpolation instructions) · `msg.refusal` check → `AIRefusalError` · error classes (`AIRefusalError`, `AISchemaError`, `AIAuthError`, `AITimeoutError`, `AIServiceError`) · image+result persistence to `AI_IMAGE_STORAGE_PATH/<date>/<ts>_<sha>.{jpg,json}` · `startup()` / `shutdown()` for SDK client lifecycle and retention pruning |
| [x] 16.1.5 | `src/backend/main.py` | Lifespan: `await ai.startup()` / `await ai.shutdown()` |

**Verify:** `uvicorn main:app` starts without errors when `AI_API_KEY` empty (feature degrades gracefully).

### 16.2 Backend – `/api/analyze-image` endpoint

| # | File | Content |
|---|------|---------|
| [x] 16.2.1 | `src/backend/main.py` | `POST /api/analyze-image` route: `UploadFile` form; auth dependency; MIME allow-list (jpeg, png, webp); byte cap; `ai_rate_check_and_increment()`; map AI exceptions → `AIRefusalError`/`AISchemaError`→422, `AIAuthError`→502, `AITimeoutError`/`AIServiceError`→503; return `ph`, `cl`, `warnings`, `image`, `requestsRemainingToday` |
| [x] 16.2.2 | `src/backend/main.py` | Extend `GET /api/status` with `aiConfigured`, `imageAnalysisRequestsToday` |

**Verify:** `curl -F image=@strip.jpg -H "Authorization: Bearer ..." /api/analyze-image` → 200 with extracted values (against mocked AI in tests).

### 16.3 Backend – Tests

| # | File | Test cases |
|---|------|------------|
| [x] 16.3.1 | `src/backend/tests/test_ai.py` | Happy path (SDK mock returns valid parsed response) → `ImageAnalysisResult` · `msg.refusal` set → `AIRefusalError` · `ValidationError` on parsed → `AISchemaError` · SDK `AuthenticationError` → `AIAuthError` · SDK `TimeoutError` → `AITimeoutError` · file is persisted to storage path · image hash dedup |
| [x] 16.3.2 | `src/backend/tests/test_api.py` | `POST /api/analyze-image`: 200 valid · 400 wrong MIME · 400 oversized · 401 missing token · 422 on `AIRefusalError` · 429 after `AI_MAX_REQUESTS_PER_DAY` reached · 503 on timeout · counter rolls over at UTC midnight (mock `datetime`) |
| [x] 16.3.3 | `src/backend/tests/conftest.py` | Add fixtures: temp `AI_IMAGE_STORAGE_PATH` (`tmp_path`), patch `ai.analyze_pool_image` per test, reset `_ai_counter` between tests |

**Verify:** `pytest -v` → all tests green incl. new AI tests.

### 16.4 Frontend – Image capture & API call

| # | File | Content |
|---|------|---------|
| [x] 16.4.1 | `src/frontend/src/composables/useImage.js` | `compress(file, {maxEdge, quality})` using `createImageBitmap` + `OffscreenCanvas`, returns JPEG `File` |
| [x] 16.4.2 | `src/frontend/src/composables/useApi.js` | `analyzeImage(file)`: builds `FormData` (image only), POST `/api/analyze-image`, no manual `Content-Type`, distinguishes 401/422/429/5xx |
| [x] 16.4.3 | `src/frontend/src/components/ImageCaptureModal.vue` | `<input type="file" accept="image/*" capture="environment">` (rear camera on mobile) · loading overlay · error display · checks for -1 values (shows error, does not apply) · warnings → toast alert · emits `applied({pH, cl, image})` |
| [x] 16.4.4 | `src/frontend/src/components/MeasurementForm.vue` | "Analyze Photo" button between pool select and temperature; opens modal; on `applied` → merge values into form state + success toast |
| [x] 16.4.5 | `src/frontend/src/composables/useToast.js` | (no change – reuse) |

**Verify:** `npm run dev` → tap button → camera opens → selected image shows preview, loading state, fields prefilled with mocked backend response.

### 16.5 Frontend – Tests

| # | File | Test cases |
|---|------|------------|
| [x] 16.5.1 | `src/frontend/tests/useImage.spec.js` | Long-edge clamp respected · output is `image/jpeg` · output bytes < input bytes for an oversized fixture · throws on non-image file |
| [x] 16.5.2 | `src/frontend/tests/useApi.spec.js` (new) | `analyzeImage` builds correct `FormData`, sets only `Authorization` header, maps 401/422/429/5xx to distinct error strings (use `vi.fn()` on `fetch`) |

**Verify:** `npm run test` → all tests green.

### 16.6 Infrastructure

| # | File | Content |
|---|------|---------|
| [x] 16.6.1 | `src/docker-compose.yml` | Add bind mount `./data/ai:/data/ai` on the backend service |
| [x] 16.6.2 | `src/docker-compose.yml` | Pass new AI env vars to the backend service (`env_file: .env` already covers them) |
| [x] 16.6.3 | `src/Caddyfile` | Increase `request_body max_size 12MB` for `/api/analyze-image` route only |

**Verify:** `docker compose config` clean; volume persists across `docker compose down && up`.

### 16.7 End-to-end integration

| # | Step | Expected result |
|---|------|-----------------|
| [x] 16.7.1 | `.env`: set real `AI_API_KEY`, `AI_PROVIDER`, `AI_MODEL` | Backend logs "AI configured" |
| [x] 16.7.2 | Open PWA on phone, tap "Analyze Photo" | Camera opens, photo capture works |
| [x] 16.7.3 | Submit a test-strip photo | Form pH/cl prefilled within < 15 s; toast "Values extracted – please verify" |
| [x] 16.7.4 | Repeat 11× within one day | 11th request returns 429 + toast "Daily image-analysis limit reached" |
| [x] 16.7.5 | Inspect `AI_IMAGE_STORAGE_PATH` | Image + JSON pair stored per request, dated subdirectory |
| [x] 16.7.6 | Manually edit prefilled values, press SEND | Measurement reaches MQTT topic with corrected values |

**Verify:** Full flow works end-to-end; failure modes (rate limit, timeout) degrade gracefully to manual entry.

### 16.8 Developer tool: Test script `test/test_openrouter.py`

| # | File | Content |
|---|------|---------|
| [x] 16.8.1 | `test/test_openrouter.py` | Standalone connectivity test: text + image analysis; loads defaults from `src/.env` with env override; resizes images to configurable max dimension via Pillow; sums total costs via generation endpoint |
| [x] 16.8.2 | `src/backend/requirements.txt` | Add `Pillow>=11.0` for image resizing |

### 16.9 Developer tool: Benchmark script `test/benchmark_openrouter.py`

| # | File | Content |
|---|------|---------|
| [x] 16.9.1 | `test/benchmark_openrouter.py` | Benchmark script: reads ground truth values, runs OpenRouter AI analysis on multiple test-strip images, computes accuracy score for pH & Cl, detects warnings mismatches with penalty, and aggregates total/estimated costs |
| [x] 16.9.2 | `test/benchmark_openrouter.py` | Env vars `AI_BENCHMARK_LIMIT`, `AI_PH_TOLERANCE`, `AI_CL_TOLERANCE`, `AI_CL_TOLERANCE_STOPS`; log-scale Cl scoring via "stops"; image size display (px + KB); -1 return for uncertain values with scoring: both -1 → 100%, mismatch → 0% |


---


## Phase 17 – Feature: AI Result & Image Traceability in MQTT

Goal: The app remembers AI analysis results (pH, cl) and image filenames, and sends them alongside
the (possibly corrected) values in the MQTT message. This enables later analysis of AI accuracy
and how often manual corrections are needed.

| # | File | Content |
|---|------|---------|
| [x] 17.1 | `src/backend/ai.py` | `_persist_image()` returns relative image path; `analyze_pool_image()` sets `result.image` for traceability |
| [x] 17.2 | `src/backend/main.py` | Add optional `aiPH`, `aiCL`, `aiImage`, `aiCorrected` fields to `Measurement` model; `build_mqtt_payload()` includes them when present; `/api/analyze-image` returns `image` field |
| [x] 17.3 | `src/frontend/src/composables/useApi.js` | `postMeasurement()` forwards `aiPH`, `aiCL`, `aiImage`, `aiCorrected` from form to API payload |
| [x] 17.4 | `src/frontend/src/components/ImageCaptureModal.vue` | Emit `image` filename in `applied` event |
| [x] 17.5 | `src/frontend/src/components/MeasurementForm.vue` | Track `aiData` (ph, cl, image) on capture; compute `aiCorrected` flag on submit by comparing form vs AI values; include all AI fields in payload; reset AI data on form reset |
| [x] 17.6 | `src/backend/tests/test_models.py` | Tests: AI fields default to None, AI fields with values, aiCorrected=False |
| [x] 17.7 | `src/backend/tests/test_api.py` | Tests: measurement with AI fields published correctly in MQTT payload |

**Verify:** `pytest -v` → all 56 tests green. `npm run test` → pre-existing validation.spec.js failures unrelated.


---


## Phase 18 – Integration: mqtt2mail Service

Goal: mqtt2mail runs as an integrated Docker service and can automatically subscribe
to topics from the pool config (`POOL_LIST`).

| # | File | Content |
|---|------|---------|
| [x] 18.1 | `src/mqtt2mail/app/mqtt2mail.py` | Topic resolution: `MQTT_TOPICS*` -> `POOL_LIST` -> `MQTT_TOPIC_BASE`; fallback for `MQTT_USER/MQTT_PASS`; multi-topic subscribe; time-based reports via `REPORT_TIMES` (fallback: `REPORT_INTERVAL_MINUTES`) |
| [x] 18.2 | `src/mqtt2mail/Dockerfile` | Script copied into image (`COPY app/mqtt2mail.py`) |
| [x] 18.3 | `src/docker-compose.yml` | Service `mqtt2mail_pool` with `depends_on: mosquitto`, resource limits, `MQTT_TOPICS` env |
| [x] 18.4 | `src/.env.example`, `src/mqtt2mail/.env.example` | Shared mqtt2mail environment variables documented |
| [x] 18.5 | `src/deploy-prepare.sh` | mqtt2mail files included in deployment package |
| [x] 18.6 | `README.md`, `src/mqtt2mail/README.md` | Project-wide usage and topic configuration documented |
| [x] 18.7 | `src/mqtt2mail/app/mqtt2mail.py`, `.env.example` files | Email sending always active (stdout fallback on error); startup test mail; report timing via `REPORT_TIMES` or `REPORT_INTERVAL_MINUTES` |
| [x] 18.8 | `src/mqtt2mail/app/mqtt2mail.py` | Fix disconnect loop: random client ID suffix, `reconnect_delay_set(min_delay=30)`, `on_subscribe` callback, paho debug logging |


---


## Phase 19 – Feature: Chemieupdate (B1)

Goal: Add a dedicated chemistry update page and backend endpoint to log one chemical
addition event per entry with optional amount and enum unit.

| # | File | Content |
|---|------|---------|
| [x] 19.1 | `docs/Pool-Monitoring - Functional Specification (FSD).md` | Rewrite Chemieupdate specification with clean wording: navigation (burger menu), UI wireframes, API contract `POST /api/chem`, topic suffix `/chem`, enum mapping (DE -> EN), and `amount`/`unit` pair rule |
| [x] 19.2 | `docs/Pool-Monitoring - Technical Specification (TSD).md` | Align technical design with FSD rewrite: view state (`form\|chemistry\|settings`), component responsibilities, chemistry API payload, and MQTT payload constraints (chem payload without `sensorType`) |
| [x] 19.3 | `src/backend/main.py` | Add `ChemicalUpdate` model + validators (`chemicalType` enum, `unit` enum, `amount`/`unit` pair rule) and `POST /api/chem` route |
| [x] 19.4 | `src/backend/main.py` | Add `build_chemical_payload()` and publish to `<pool-topic>/chem`; remove `sensorType` from chemistry MQTT payload |
| [x] 19.5 | `src/backend/tests/test_models.py`, `src/backend/tests/test_api.py` | Add tests for `ChemicalUpdate` validation, route status codes (201/401/422/503), topic suffix `/chem`, and payload shape |
| [x] 19.6 | `src/frontend/src/App.vue` | Add third view state (`chemistry`) and navigation between measurement and chemistry forms (without Vue Router) |
| [x] 19.7 | `src/frontend/src/components/ChemicalUpdateForm.vue` | New form: datetime, pool, chemical type, optional amount + unit, inline validation, toast feedback |
| [x] 19.8 | `src/frontend/src/composables/useApi.js` | Add `postChemicalUpdate()` with auth header and error mapping |
| [x] 19.9 | `src/frontend/tests/useApi.spec.js` (+ optional component spec) | Add frontend tests for chemistry API call and error paths |

**Verify:** `cd src/backend && pytest -v` and `cd src/frontend && npm run test` green; manual flow publishes chemistry event to `.../chem` topic.


---

## Phase 20 – Feature: Live Data (MQTT Subscribe + Live View + Trend Chart)

Goal: Backend subscribes to sensor + pump MQTT topics, aggregates per-hour mean into SQLite, and persists every pump-state change. Frontend adds a `Live` view (default landing page) with a modern dashboard (current temperature as main value, pH/Cl as 5-sample averages from RAM, pump status as icons) and a zoomable 7-day trend chart of temperature, pH, and chlorine.

Architecture: all incoming topics derive from `POOL_LIST` via configurable templates
(`LIVE_TOPIC_BLE_TEMPLATE`, `LIVE_TOPIC_PUMP_TEMPLATE`). Aggregation is a per-hour mean
of the rolling in-memory ring buffer; pump events are persisted only on actual state
change. Frontend polls `GET /api/live` every 30 s; chart data comes from `GET /api/history`
(one call per metric, 1-hour buckets).

### 20.1 ENV and configuration surface

| # | File | Content |
|---|------|---------|
| [x] 20.1.1 | `src/.env.example` | New env block `LIVE_*`: `LIVE_TOPIC_BLE_TEMPLATE=home/{pool}/pool/ble-yc01`, `LIVE_TOPIC_PUMP_TEMPLATE=home/{pool}/pool/pump`, `LIVE_AGGREGATION_WINDOW_MINUTES=60`, `LIVE_RETENTION_DAYS=90`, `LIVE_DB_PATH=/data/live/live.db`, `LIVE_SAMPLE_RING_SIZE=5`, `LIVE_STALE_AFTER_SECONDS=600`, `LIVE_PUMP_FIELD_MAIN=mainPump`, `LIVE_PUMP_FIELD_SOLAR=solarPump`, `LIVE_PUMP_FIELD_TIME=time` |
| [x] 20.1.2 | `src/.gitignore` | Ignore `data/live/` local dev DB |

**Verify:** `.env.example` contains the new block; restart picks up defaults.

### 20.2 Backend: SQLite layer (`db.py`)

| # | File | Content |
|---|------|---------|
| [x] 20.2.1 | `src/backend/db.py` | New module. `init_db(path)` opens SQLite, `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, `PRAGMA foreign_keys=ON`, `check_same_thread=False`. Schema (idempotent `CREATE TABLE IF NOT EXISTS`): `live_aggregates(pool TEXT, metric TEXT, hour_start INTEGER, value REAL, sample_count INTEGER, PRIMARY KEY(pool,metric,hour_start))`; index on `hour_start`. `pump_events(id INTEGER PK AUTOINCREMENT, pool TEXT, pump TEXT, state INTEGER, time INTEGER, received_at INTEGER)`; index on `time`. Functions: `insert_aggregate(pool, metric, hour_start, value, n)`, `insert_pump_event(pool, pump, state, time, received_at)`, `get_aggregates(pool, metric, since_ts)`, `get_pump_events(pool, since_ts)`, `cleanup_old_rows(retention_days)`. A module-level `threading.Lock` serializes writes. |
| [x] 20.2.2 | `src/backend/tests/test_db.py` | In-memory SQLite fixture (`tmp_path`); tests: schema creation idempotent, insert/get aggregate roundtrip, insert/get pump event roundtrip, cleanup deletes rows older than `retention_days`, primary-key conflict on duplicate `(pool, metric, hour_start)` is a no-op (UPSERT via `INSERT OR REPLACE`) |

**Verify:** `pytest -v src/backend/tests/test_db.py` green.

### 20.3 Backend: in-memory live state (`live_state.py`)

| # | File | Content |
|---|------|---------|
| [x] 20.3.1 | `src/backend/live_state.py` | Thread-safe `LiveState` class. `push_sample(pool, metric, value, ts)`: appends to per-metric ring of max `ring_size` (default 5), updates `last_value` + `last_ts`. `set_pump(pool, name, state, ts) -> bool`: returns `True` only on actual change; updates internal state. `get_snapshot(pool) -> dict`: returns `{ts, temp, pH, cl, pump, stale}` where pH/Cl = mean of ring, `stale = (now - last_ts) > stale_after`. `get_known_pools() -> list[str]`. All access guarded by a single `threading.Lock` (paho callback runs in a worker thread). |
| [x] 20.3.2 | `src/backend/tests/test_live_state.py` | Tests: ring buffer caps at `ring_size`; pump change detection (same state → no event, different state → event); stale flag flips after threshold; per-pool isolation; 5-sample mean computed correctly |

**Verify:** `pytest -v src/backend/tests/test_live_state.py` green.

### 20.4 Backend: MQTT subscribe (`mqtt.py`)

| # | File | Content |
|---|------|---------|
| [x] 20.4.1 | `src/backend/mqtt.py` | Add module state `_subscriptions: list[tuple[str, Callable]]`. New function `subscribe(topic: str, on_message: Callable[[str, dict], None])` – registers subscription. In `on_connect` callback, re-subscribe to all registered topics (survives reconnect). Add `on_message` callback that parses JSON, routes to handler. Keep `publish()` API unchanged. |
| [x] 20.4.2 | `src/backend/tests/test_mqtt.py` | Tests using `paho.mqtt.client.Client` mocked: subscribe registers topics; reconnect re-subscribes; malformed JSON is logged and dropped |

**Verify:** `pytest -v src/backend/tests/test_mqtt.py` green.

### 20.5 Backend: aggregator background task (`aggregator.py`)

| # | File | Content |
|---|------|---------|
| [x] 20.5.1 | `src/backend/aggregator.py` | `Aggregator` class with `start()` (returns `asyncio.Task`) and `stop()`. Loop: `await asyncio.sleep(60)`; on each tick compute the previous full hour bucket; for each (pool, metric) compute mean of ring buffer samples received in that hour and call `db.insert_aggregate(...)`. Daily at 03:00 UTC: `db.cleanup_old_rows(retention_days)`. Failures are logged, not raised (never kill the task). |
| [x] 20.5.2 | `src/backend/tests/test_aggregator.py` | Test: with a mock `db` and `live_state`, advance time to the next hour boundary; assert `insert_aggregate` called once per (pool, metric) with the correct mean and sample count; cleanup runs on day boundary; one failing insert does not abort the loop |

**Verify:** `pytest -v src/backend/tests/test_aggregator.py` green.

### 20.6 Backend: integration in `main.py` and new endpoints

| # | File | Content |
|---|------|---------|
| [x] 20.6.1 | `src/backend/main.py` | Read `LIVE_*` env vars at top with safe defaults. Import `db`, `live_state`, `aggregator`. In `lifespan`: call `db.init_db(LIVE_DB_PATH)`, instantiate `live_state.LiveState(ring_size, stale_after)`, instantiate `Aggregator`; for each pool in `POOL_LIST` subscribe to `LIVE_TOPIC_BLE_TEMPLATE.format(pool=name)` and `LIVE_TOPIC_PUMP_TEMPLATE.format(pool=name)`; on shutdown stop the aggregator. Add MQTT `on_message` dispatcher that calls `live_state.push_sample(...)` for BLE messages and `live_state.set_pump(...)` (and on change `db.insert_pump_event(...)`) for pump messages. Pump field names read from `LIVE_PUMP_FIELD_*`. |
| [x] 20.6.2 | `src/backend/main.py` | New endpoints (all `Depends(verify_token)`): `GET /api/pools/live` returns list of pool names that have at least one sample; `GET /api/live?pool=<name>` returns `live_state.get_snapshot(pool)` enriched with `stale_seconds`; `GET /api/history?pool=<name>&metric=temp\|pH\|cl&days=7` returns `db.get_aggregates(...)`; `GET /api/pump-events?pool=<name>&days=7` returns `db.get_pump_events(...)`. All query params validated: `pool` must be in `POOL_LIST`, `metric` ∈ {temp, pH, cl}, `days` int in 1..30. |
| [x] 20.6.3 | `src/backend/main.py` | Extend `GET /api/status` with `liveDataConfigured: bool` (true if DB path is set and `init_db` succeeded) |
| [x] 20.6.4 | `src/backend/tests/test_api_live.py` | TestClient + temp SQLite + monkey-patched `live_state`: `GET /api/live` returns snapshot shape; 401 without token; 422 on unknown pool; 422 on bad metric; history returns 168 points for 7d with 1h bucket; pump-events returns inserted events in order; `/api/pools/live` returns only pools with data |

**Verify:** `pytest -v src/backend/tests/` (all green) and `uvicorn main:app` starts without import errors when `LIVE_DB_PATH` is writable.

### 20.7 Infrastructure

| # | File | Content |
|---|------|---------|
| [x] 20.7.1 | `src/docker-compose.yml` | Add `volumes: - ./data/live:/data/live` to `backend` service. |
| [x] 20.7.2 | `src/deploy-prepare.sh` | Ensure `data/` placeholder is created in the deployment package; add `data/live/.gitkeep` so the volume mount exists on first deploy. |

**Verify:** `docker compose config` clean; container starts with writable `/data/live`.

### 20.8 Frontend: dependencies

| # | File | Content |
|---|------|---------|
| [x] 20.8.1 | `src/frontend/package.json` | Add dependencies `chart.js@^4.4` and `chartjs-plugin-zoom@^2.0`. Update `npm install`. |
| [x] 20.8.2 | `src/frontend/src/main.js` | Import `chartjs-plugin-zoom` once (auto-registers on `Chart.register()`). |

**Verify:** `npm run build` succeeds; bundle includes Chart.js.

### 20.9 Frontend: API composable extensions

| # | File | Content |
|---|------|---------|
| [x] 20.9.1 | `src/frontend/src/composables/useApi.js` | Add `fetchPoolsLive() -> [{name, hasData}]` (GET `/api/pools/live`), `fetchLive(pool) -> {ts, temp, pH, cl, pump, stale, staleSeconds}`, `fetchHistory(pool, metric, days) -> {metric, unit, points: [{t, v}]}`, `fetchPumpEvents(pool, days) -> {events: [...]}`. All send `Authorization: Bearer`. Differentiate 401/422/network. |
| [x] 20.9.2 | `src/frontend/tests/useApi.spec.js` | Add tests for the four new methods (success, 401, 422 on unknown pool, network error). |

**Verify:** `npm run test` green for useApi.

### 20.10 Frontend: live-data composable

| # | File | Content |
|---|------|---------|
| [x] 20.10.1 | `src/frontend/src/composables/useLiveData.js` | Module-level singleton state (`snapshot`, `loading`, `error`, `lastFetch`). `start(pool, {intervalMs=30000, onError})` schedules `setInterval` calling `fetchLive(pool)`; updates state; clears on `stop()`. Exposes `stale` computed from `staleSeconds` and a `usingCached` flag if last fetch failed. |
| [x] 20.10.2 | `src/frontend/tests/useLiveData.spec.js` | Use vitest fake timers. Test: `start` triggers first fetch immediately, then every `intervalMs`; `stop` clears interval; on fetch error the error is exposed and polling continues; `stale` computed property correct. |

**Verify:** `npm run test` green.

### 20.11 Frontend: `PumpStatusCard.vue`

| # | File | Content |
|---|------|---------|
| [x] 20.11.1 | `src/frontend/src/components/PumpStatusCard.vue` | Props: `pump` (String: `'main'` / `'solar'`), `state` (Boolean), `runningSince` (Number | null). Display: large icon (gear for main, sun for solar), label (HAUPTPUMPE / SOLARPUMPE), status text (LÄUFT / AUS), and "läuft seit X min" if `runningSince` known. Color tokens: running = `bg-success/10 text-success border-success/30`, idle = `bg-slate-100 text-slate-500`. Touch target ≥ 44×44 px. |

**Verify:** Component renders for both states; no business logic in template beyond display.

### 20.12 Frontend: `LiveView.vue`

| # | File | Content |
|---|------|---------|
| [x] 20.12.1 | `src/frontend/src/components/LiveView.vue` | Composition API. On mount: load `pools = await fetchPoolsLive()`, default to first pool, call `useLiveData().start(pool)`. Template: pool selector (if >1 pool), last-update timestamp, big "Temperatur" card (large number, °C, stale badge if `stale`), two side cards pH/Cl (5-sample mean + "Ø 5 M."), two `PumpStatusCard` instances, then `<TrendChart :pool="pool" />` below. Cleanup in `onBeforeUnmount` calling `stop()`. Handle empty/error state ("Warte auf Daten..." if no snapshot yet, or "Verbindung fehlgeschlagen" with retry button on persistent error). |
| [x] 20.12.2 | `src/frontend/tests/LiveView.spec.js` | Render test: with mock `useLiveData` returning a known snapshot, all cards show correct values; pool selector lists pools; cleanup is called on unmount (use vi.fn for `stop`). |

**Verify:** `npm run test` green; manual test against running backend shows live values.

### 20.13 Frontend: `TrendChart.vue`

| # | File | Content |
|---|------|---------|
| [x] 20.13.1 | `src/frontend/src/components/TrendChart.vue` | Props: `pool` (String). On `pool` change and on mount: fetch `fetchHistory(pool, 'temp', 7)`, `fetchHistory(pool, 'pH', 7)`, `fetchHistory(pool, 'cl', 7)` in parallel. Build a single Chart.js line chart with 3 datasets (temp → primary blue, pH → success green, cl → warning amber), 3 Y-axes (left: temp °C, right: pH, right-inner: cl), X axis = time (last 7d, day ticks). Plugins: legend, tooltip (touch enabled), `chartjs-plugin-zoom` with `pinch` + `wheel` zoom and `pan`. Empty state: "Noch keine Daten". Resize observer to redraw on container size change. |
| [x] 20.13.2 | `src/frontend/tests/TrendChart.spec.js` | Mock `fetchHistory`. Render test: 3 datasets created; empty state shown when no points; chart instance destroyed in `onBeforeUnmount` (no memory leak). |

**Verify:** `npm run test` green; manual test shows 3 lines, zoom on touch works.

### 20.14 App shell integration

| # | File | Content |
|---|------|---------|
| [x] 20.14.1 | `src/frontend/src/App.vue` | Add `{ label: 'Live', view: 'live' }` as first entry in `navigationEntries`. Change `const view = ref('live')` (default = live). Add `<div v-show="view === 'live'"><LiveView /></div>` block. Reuse the existing header + burger menu + settings pattern. |
| [x] 20.14.2 | `src/frontend/src/App.vue` | Add `import LiveView from './components/LiveView.vue'`. |

**Verify:** App opens to Live view by default; burger menu lists Live / Measurements / Chemieupdate / Settings.

### 20.15 End-to-end test

| # | Step | Expected result |
|---|-------|-----------------|
| [x] 20.15.1 | Start stack (`docker compose up -d`) | All services healthy |
| [x] 20.15.2 | `mosquitto_pub -h localhost -p 2883 -t home/H32/pool/ble-yc01 -m '{"temp":28.4,"pH":7.2,"cl":0.7}'` | Backend log shows message received; `sqlite3 data/live/live.db "SELECT * FROM live_aggregates"` (after 1h) shows row |
| [x] 20.15.3 | `mosquitto_pub -h localhost -p 2883 -t home/H32/pool/pump -m '{"mainPump":true,"solarPump":false,"time":1755724982}'` | `SELECT * FROM pump_events` shows one event |
| [x] 20.15.4 | Open `https://<host>/` in browser | Live view loads; temperature shows 28.4; pH 7.2; cl 0.7; main pump = LÄUFT; chart empty (no aggregates yet) |
| [x] 20.15.5 | Wait 30 s | Live view auto-refreshes (timestamp updates) |
| [x] 20.15.6 | Publish pump state change to `false` | `pump_events` has 2 rows; UI updates within 30 s |

**Verify:** Full E2E flow green.

### 20.16 Plan + docs sync

| # | File | Content |
|---|------|---------|
| [x] 20.16.1 | `docs/plan.md` | All checkboxes in Phase 20 set as completed |
| [x] 20.16.2 | `docs/Pool-Monitoring - Functional Specification (FSD).md` | New section 3.4 "Live View": pool selector, temperature main card, pH/cl side cards (5-sample mean), pump status cards, 7-day trend chart, stale behavior, polling cadence. Navigation dropdown gets new entry "Live" as default landing. |
| [x] 20.16.3 | `docs/Pool-Monitoring - Technical Specification (TSD).md` | New sections covering: 4.3 Live-View component contract, 5.8 `db.py` (SQLite + WAL), 5.9 `live_state.py` (ring buffer, pump state change), 5.10 `aggregator.py` (hourly rollup + retention), 5.11 new endpoints `/api/pools/live`, `/api/live`, `/api/history`, `/api/pump-events`. Update directory tree (Phase 20) and explicitly promote Chart.js from "Future Enhancement" to "Phase 20 dependency". |

**Verify:** `git diff --stat` shows only docs; TSD §2 reflects the dependency promotion.


## File Overview

```
src/
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Caddyfile
├── deploy-prepare.sh
    ├── backend/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── pyproject.toml
    │   ├── main.py
    │   ├── mqtt.py
    │   ├── ai.py                          # Phase 16
    │   ├── db.py                          # Phase 20 (SQLite)
    │   ├── live_state.py                  # Phase 20 (in-memory state)
    │   ├── aggregator.py                  # Phase 20 (hourly rollup)
    │   └── tests/
    │       ├── conftest.py
    │       ├── test_models.py
    │       ├── test_api.py
    │       ├── test_auth.py
    │       ├── test_ai.py                 # Phase 16
    │       ├── test_db.py                 # Phase 20
    │       ├── test_live_state.py         # Phase 20
    │       ├── test_mqtt.py               # Phase 20
    │       ├── test_aggregator.py         # Phase 20
    │       └── test_api_live.py           # Phase 20
    ├── mqtt2mail/                         # Phase 18
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── .env.example
    │   ├── README.md
    │   └── app/
    │       └── mqtt2mail.py
    └── frontend/
        ├── Dockerfile
        ├── Dockerfile_production
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
        │   │   ├── ValueSliderInput.vue   # Phase 7
        │   │   ├── MeasurementForm.vue
        │   │   ├── ImageCaptureModal.vue  # Phase 16
        │   │   ├── ChemicalUpdateForm.vue # Phase 19
        │   │   ├── LiveView.vue           # Phase 20
        │   │   ├── TrendChart.vue         # Phase 20
        │   │   ├── PumpStatusCard.vue     # Phase 20
        │   │   └── SettingsPanel.vue
        │   └── composables/
        │       ├── useSettings.js
        │       ├── useApi.js
        │       ├── useCamera.js           # Phase 16
        │       ├── useImage.js            # Phase 16
        │       ├── useToast.js
        │       └── useLiveData.js         # Phase 20
        └── tests/
            ├── validation.spec.js
            ├── useSettings.spec.js
            ├── StepperInput.spec.js
            ├── useImage.spec.js           # Phase 16
            ├── useApi.spec.js             # Phase 16
            ├── useLiveData.spec.js        # Phase 20
            ├── LiveView.spec.js           # Phase 20
            └── TrendChart.spec.js         # Phase 20
    ```
