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
| [x] 20.1.1 | `src/.env.example` | New env block `LIVE_*`: `LIVE_TOPIC_BLE_TEMPLATE=home/{pool}/pool/ble-yc01`, `LIVE_TOPIC_PUMP_TEMPLATE=home/{pool}/pool/pump`, `LIVE_AGGREGATION_WINDOW_MINUTES=60`, `LIVE_RETENTION_DAYS=90`, `LIVE_DB_PATH=/data/history/data.db`, `LIVE_SAMPLE_RING_SIZE=5`, `LIVE_STALE_AFTER_SECONDS=600`, `LIVE_PUMP_FIELD_MAIN=mainPump`, `LIVE_PUMP_FIELD_SOLAR=solarPump`, `LIVE_PUMP_FIELD_TIME=time` |
| [x] 20.1.2 | `src/.gitignore` | Ignore `data/history/` local dev DB |

**Verify:** `.env.example` contains the new block; restart picks up defaults.

### 20.2 Backend: SQLite layer (`db.py`)

| # | File | Content |
|---|------|---------|
| [x] 20.2.1 | `src/backend/db.py` | New module. `init_db(path)` opens SQLite, `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, `PRAGMA foreign_keys=ON`, `check_same_thread=False`. Schema (idempotent `CREATE TABLE IF NOT EXISTS`): `live_aggregates(pool TEXT, metric TEXT, timewindow_start INTEGER, value REAL, sample_count INTEGER, PRIMARY KEY(pool,metric,timewindow_start))`; index on `timewindow_start`. `pump_events(id INTEGER PK AUTOINCREMENT, pool TEXT, pump TEXT, state INTEGER, time INTEGER, received_at INTEGER)`; index on `time`. Functions: `insert_aggregate(pool, metric, timewindow_start, value, n)`, `insert_pump_event(pool, pump, state, time, received_at)`, `get_aggregates(pool, metric, since_ts)`, `get_pump_events(pool, since_ts)`, `cleanup_old_rows(retention_days)`. A module-level `threading.Lock` serializes writes. |
| [x] 20.2.2 | `src/backend/tests/test_db.py` | In-memory SQLite fixture (`tmp_path`); tests: schema creation idempotent, insert/get aggregate roundtrip, insert/get pump event roundtrip, cleanup deletes rows older than `retention_days`, primary-key conflict on duplicate `(pool, metric, timewindow_start)` is a no-op (UPSERT via `INSERT OR REPLACE`) |

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
| [x] 20.7.2 | `src/deploy-prepare.sh` | Ensure `data/` placeholder is created in the deployment package; add `data/history/.gitkeep` so the volume mount exists on first deploy. |

**Verify:** `docker compose config` clean; container starts with writable `/data/live`.

### 20.8 Frontend: dependencies

| # | File | Content |
|---|------|---------|
| [x] 20.8.1 | `src/frontend/package.json` | Add dependency `uplot@^1.6` (replaces `chart.js` + `chartjs-plugin-zoom` + `chartjs-adapter-date-fns` + `date-fns`). Update `npm install`. |
| [x] 20.8.2 | `src/frontend/src/main.js` | Removed Chart.js plugin registration. uPlot needs no global setup — imported per-component. |

**Verify:** `npm run build` succeeds; bundle is ~33% smaller (168 KB vs 254 KB) and includes uPlot.

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
| [x] 20.13.1 | `src/frontend/src/components/TrendChart.vue` | Props: `pool` (String). On `pool` change and on mount: fetch `fetchHistory(pool, 'temp', 7)`, `fetchHistory(pool, 'pH', 7)`, `fetchHistory(pool, 'cl', 7)` in parallel. Build **3 separate uPlot instances** (one per metric) for cleaner layout and per-metric Y-axis. Each uPlot has its own Y-axis (unit shown as label). X axis = time (last 7d). Cross-chart X-axis sync via `uPlot.sync(SYNC_KEY)` + `cursor.sync.scales: ['x', null]`. **Custom `splits` callback** aligns ticks to 0h (midnight) boundaries using an adaptive step (2h / 4h / 6h / 12h / 24h / 48h depending on visible span). **Custom `values` callback** formats labels: date (`dd.MM`) at 0h ticks, time (`HH:mm`) elsewhere. **Custom wheel-zoom plugin** zooms the X axis around the cursor while the mouse is over the chart (no modifier key needed). `cursor.drag` for pan + box-zoom (built-in). Empty state: "Noch keine Daten". Resize observer to redraw on container size change. |
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
| [x] 20.15.2 | `mosquitto_pub -h localhost -p 2883 -t home/H32/pool/ble-yc01 -m '{"temp":28.4,"pH":7.2,"cl":0.7}'` | Backend log shows message received; `sqlite3 data/history/data.db "SELECT * FROM live_aggregates"` (after 1h) shows row |
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


---

## Phase 21 – Live Data Polish (debug logging, dynamic history, rate-limit)

Goal: Make the live-data path observable in DEBUG, remove the rate-limit
collision between polling reads and the per-IP middleware, refactor the
aggregator from fixed-hour to configurable-window rollups, and give the
trend chart infinite-scroll history with synchronized zoom/pan.

### 21.1 Observability – `LOG_LEVEL` end-to-end

| # | File | Content |
|---|------|---------|
| [x] 21.1.1 | `src/backend/main.py` | `LOG_LEVEL` env read at startup, `logging.basicConfig(level=…, format=…)` so root + child loggers respect it |
| [x] 21.1.2 | `src/backend/mqtt.py` | `logging.debug("MQTT recv: topic=%s payload=%s", ...)` in `_on_message` |
| [x] 21.1.3 | `src/backend/db.py` | `log.debug("DB write: measurements ...")` and `("DB write: pump_events ...")` in the insert helpers |
| [x] 21.1.4 | `src/backend/aggregator.py` | `log.debug("aggregator collect: ...")` and `("aggregator flush: ...")` |
| [x] 21.1.5 | `src/.env.example` | Document `LOG_LEVEL=INFO` default |

**Verify:** `LOG_LEVEL=DEBUG docker compose up` shows per-MQTT-message, per-aggregator-tick and per-DB-write lines.

### 21.2 Aggregator – configurable window (was hard-coded 1h)

| # | File | Content |
|---|------|---------|
| [x] 21.2.1 | `src/backend/aggregator.py` | New `window_minutes` constructor param (default 60), `tick_seconds` default 30; replaced `_rollup_window` with `_collect` (drains ring buffer into `_pending` keyed by `(pool, metric, ts)`) + `_flush_window` (writes one mean per window). Removes broken `max(60, …)` floor → now `max(1, …)` |
| [x] 21.2.2 | `src/backend/main.py` | Pass `window_minutes=LIVE_AGGREGATION_WINDOW_MINUTES` to the Aggregator |
| [x] 21.2.3 | `src/backend/tests/test_aggregator.py` | Update tests to the new `_collect` / `_flush_window` API; cover multi-window flushing and dedup via `_last_read_ts` |
| [x] 21.2.4 | `src/backend/live_state.py` | No behaviour change; only docstring tweak |

**Verify:** `LIVE_AGGREGATION_WINDOW_MINUTES=1` startup log shows `window=60s`; rows appear in `measurements` every 60 s.

### 21.3 History API – `before_ts` for backfill

| # | File | Content |
|---|------|---------|
| [x] 21.3.1 | `src/backend/db.py` | New `get_aggregates_range(pool, metric, start_ts, end_ts)` |
| [x] 21.3.2 | `src/backend/main.py` | `GET /api/history` accepts optional `before_ts` (ge=0); returns rows with `timewindow_start < before_ts` |
| [x] 21.3.3 | `src/frontend/src/composables/useApi.js` | `fetchHistory(pool, metric, days, beforeTs = null)` appends `&before_ts=…` |
| [x] 21.3.4 | `src/backend/tests/test_db.py` | Roundtrip test for the bounded range query |

**Verify:** `curl '/api/history?pool=Pool&metric=temp&days=7&before_ts=1700000000'` returns rows strictly older than that timestamp.

### 21.4 Rate-limit – exempt polling reads

| # | File | Content |
|---|------|---------|
| [x] 21.4.1 | `src/backend/main.py` | New env vars `API_RATE_LIMIT_REQUESTS=60`, `API_RATE_LIMIT_WINDOW_SECONDS=60`; new `RATE_LIMIT_EXEMPT_PREFIXES = ("/api/history", "/api/pump-events", "/api/live")` – middleware skips these so chart polls + 60 s auto-refresh + pan backfill never trip 429 |

**Verify:** Rapid panning/zooming in the trend chart yields no 429s; the middleware still throttles write endpoints.

### 21.5 TrendChart – zoom, pan, sync, backfill, future-cap (uPlot)

| # | File | Content |
|---|------|---------|
| [x] 21.5.1 | `src/frontend/src/components/TrendChart.vue` | **uPlot built-in:** `cursor.drag: { x: true, y: false }` for click-and-drag pan + box-zoom, `cursor.sync: { key, scales: ['x', null] }` for cross-chart X-axis sync via `uPlot.sync(SYNC_KEY)`. **Custom wheel-zoom plugin** (`wheelZoomPlugin`): zooms X axis around cursor when mouse is over chart, no modifier needed. Double-click listener on each chart calls `u.setScale('x', { min: firstVisible, max: capSec })` to reset to 7d window. |
| [x] 21.5.2 | `src/frontend/src/components/TrendChart.vue` | `backfillIfNeeded()` triggered on `setScale` hook. Loops over all 3 metrics, fetches `before_ts = earliestTs[metric]` whenever the visible left edge is within 2 h of the oldest loaded point. Filters response to only include points older than the current oldest (prevents infinite refetch loops). Preserves the user's visible window by passing `resetScales=false` to `setData`. `backfillInFlight` guard prevents recursion. |
| [x] 21.5.3 | `src/frontend/src/components/TrendChart.vue` | Module-level `capSec = floor(Date.now() / 1000)`; updated to `max(now, last_point)` after each `reload()`. Enforced by clamping `u.scales.x.max` in `reload()` so panning/zooming past the latest data point (or "now") is blocked. Auto-refresh shifts the visible range left so the user never sees a jump. |
| [x] 21.5.4 | `src/frontend/src/components/TrendChart.vue` | Initial `setInterval(reload, 60_000)` with `resetWindow=false` → auto-refresh keeps current zoom/pan. |
| [x] 21.5.5 | `src/frontend/tests/TrendChart.spec.js` | Adapted to uPlot API: stubs `getBoundingClientRect`, `HTMLCanvasElement.getContext` (jsdom), `Path2D`, `ResizeObserver`, and `window.matchMedia` via `tests/setup.js` (global vitest setup). Tests cover: empty state, 3 chart containers rendered, clean unmount. |

**Verify:** Panning left dynamically loads older data for all 3 metrics; panning right stops at "now"; 60 s auto-refresh doesn't reset zoom. **0h-tick alignment guaranteed** by custom `splits` callback (no more "undefined" labels from chart.js auto-tick-rounding).

### 21.5.1 TrendChart – UX polish (custom pan, manual sync, date anchor)

| # | File | Content |
|---|------|---------|
| [x] 21.5.1.1 | `src/frontend/src/components/TrendChart.vue` | **Custom pan** via `panZoomPlugin`: mousedown (capture phase + `stopImmediatePropagation` so uPlot's own handler does not run), mousemove/mouseup on `window` so the gesture is not lost when the cursor leaves the chart. `cursor.drag: { setScale: false }` disables uPlot's box-zoom (which would otherwise steal left-drag and never trigger sync). Right-edge clamp against `capSec` so panning past "now" is blocked. |
| [x] 21.5.1.2 | `src/frontend/src/components/TrendChart.vue` | **Manual X-axis sync** via `broadcastScale()`: setScale hook on the source chart calls it, it loops over the other two and calls `setScale('x', {min, max})`. `isPropagating` flag suppresses recursive broadcast + backfill in the sibling hooks. Replaces the old `uPlot.sync(SYNC_KEY)` approach, which only synced cursors, not scale. |
| [x] 21.5.1.3 | `src/frontend/src/components/TrendChart.vue` | **Date anchor on the leftmost tick** when visible span `< 86400` s: label is `"dd.MM\nHH:mm"` so the user always knows which day they are zoomed into. uPlot's `values` callback splits on `\n` and renders each part on its own line. |
| [x] 21.5.1.4 | `src/frontend/src/components/TrendChart.vue` | X-axis `rotate: 45`, `size: 60`; Y-axis `rotate: 0` (°C, pH, mg/l horizontal next to tick values). Chart container `height: 260px`, `CHART_HEIGHT = 260`. Outer template `space-y-10` (40 px between the three charts). |
| [x] 21.5.1.5 | `src/frontend/src/components/TrendChart.vue` | dblclick resets all three charts to the 7-day window in one shot, wrapped in `isPropagating = true` so the per-chart setScale hook does not re-broadcast. |
| [x] 21.5.1.6 | `src/.gitignore` | Ignore `test/*.png` so ad-hoc screenshots dropped into `test/` during development do not get tracked. |

### 21.6 LiveView UI – simplification

| # | File | Content |
|---|------|---------|
| [x] 21.6.1 | `src/frontend/src/components/LiveView.vue` | Always-visible pool selector (even for a single pool, centred as the title). Move the "Warte auf Daten…" placeholder below the snapshot template. Show the 7-day chart independently of the snapshot so users see historical context immediately. Drop the redundant "Ø 5 M." sub-label under pH/Cl cards |
| [x] 21.6.2 | `src/frontend/tests/LiveView.spec.js` | Adapt to the new template structure |

**Verify:** LiveView renders the chart even before the first snapshot; selector is the heading.

### 21.7 Infrastructure / dev

| # | File | Content |
|---|------|---------|
| [x] 21.7.1 | `src/backend/Dockerfile` | `mkdir -p /data/history && chown appuser:appuser /data/history` before `USER appuser` so the bind-mount target is writable for the non-root user |
| [x] 21.7.2 | `test/test_analyze-image.http` | Refresh to match the latest endpoint contract |

**Verify:** Fresh `docker compose up` succeeds; no permission errors writing to `/data/history/data.db`.


---

## Phase 22 – TrendChart: Touch Gestures

Goal: Make the trend chart fully operable on touch devices (phone, tablet).
The chart's `panZoomPlugin` only wired mouse events (`wheel`, `mousedown`,
`mousemove`, `mouseup`); on touch, pan and zoom were completely dead. Add
single-finger pan, two-finger pinch-zoom, and double-tap reset to the
uPlot overlay (`.u-over`) so the chart matches the desktop behaviour.

### 22.1 `TrendChart.vue` – touch handler

| # | File | Content |
|---|------|---------|
| [x] 22.1.1 | `src/frontend/src/components/TrendChart.vue` | New `touchGestureHandler(u)` factory wired from the `ready` hook of `panZoomPlugin` after the existing mouse handlers. `touchstart`/`touchmove` are `passive: false` with `e.preventDefault()` so the browser does not steal the gesture as a scroll/pull-to-refresh. |
| [x] 22.1.2 | `src/frontend/src/components/TrendChart.vue` | **Single-finger pan:** `touchstart` records `{ startX, startMin, startMax, rect }`. `touchmove` converts horizontal delta to a scale delta (`dVal = -(dx / rect.width) * range`) and calls `u.setScale('x', { min, max })` in a batch. The right edge is clamped against `capSec` so panning into the future is blocked, mirroring the mouse-pan clamp. |
| [x] 22.1.3 | `src/frontend/src/components/TrendChart.vue` | **Two-finger pinch:** `touchstart` with `touches.length >= 2` records `{ startDist, centerX, centerVal, leftPct, startMin, startMax, rect }`. `touchmove` computes `factor = dist / startDist` and uses `nRange = oRange / factor` anchored at the pinch midpoint. Switching from 1 → 2 fingers drops any pending pan; the 2 → 1 transition ends the gesture (does not resume a pan, avoids accidental jumps). |
| [x] 22.1.4 | `src/frontend/src/components/TrendChart.vue` | **Double-tap reset:** second `touchstart` within `DOUBLE_TAP_MS = 300` and within `TAP_SLOP_PX = 24` of the first tap triggers `resetAllCharts()` (the same routine used by the desktop `dblclick` listener). `lastTap` is cleared on every tap so a triple-tap does not chain into a double-tap. |
| [x] 22.1.5 | `src/frontend/src/components/TrendChart.vue` | `resetAllCharts()` is now a module-scope helper used by both the `el.addEventListener('dblclick', …)` handler and the touch double-tap branch — single source of truth for the 7-day reset. |

**Verify:** On a real phone the chart pans with one finger, zooms in/out by pinching, and double-tap returns to the 7-day window. The right edge never crosses "now".

### 22.2 Tests

| # | File | Content |
|---|------|---------|
| [x] 22.2.1 | `src/frontend/tests/TrendChart.spec.js` | New `describe('TrendChart touch gestures')` block. Uses `new Event('touchstart', …)` with a `touches` array (jsdom has no `Touch` constructor) dispatched on the chart's `.u-over` overlay. Cases: single-finger `touchstart` does not `preventDefault`; two-finger `touchstart` `preventDefault`s; second tap inside the 300 ms window at the same spot `preventDefault`s; `touchmove` `preventDefault`s for both pan and pinch; a tap far outside the 24 px slop window is treated as a fresh pan (not a double-tap). |

**Verify:** `npm run test` green; 64/64 tests pass (was 59).


---

## Phase 23 – MQTT Base-Topic Consolidation

Goal: Replace the brittle topic-template model (`LIVE_TOPIC_BLE_TEMPLATE`,
`LIVE_TOPIC_PUMP_TEMPLATE`, configurable `LIVE_PUMP_FIELD_*` field names, two
separate handlers per pool) with a clean **base-topic model** where
`POOL_LIST[].topic` is the **base** topic, the backend subscribes once per pool
with a wildcard (`<base>/+`), and a single JSON-content-analysis handler
dispatches measurements, pump state, and chem-data. mqtt2mail derives its
subscriptions from `POOL_LIST` only; the mqtt-publisher uses a
`POOL_BASE_TOPICS` dict with hard-coded suffixes. Pump field names
(`mainPump`, `solarPump`, `time`) become hard-coded constants — no env
override. One source of truth, one subscription per pool, one handler.

### 23.1 Backend: Base-topic model + JSON content analysis

Goal: Collapse BLE + pump handlers into a single content-driven dispatcher.
`POOL_LIST[].topic` becomes the **base** (e.g. `home/H32/pool`); subscribe
once to `<base>/+`; inspect the JSON payload to decide whether it is a
measurement snapshot, a pump-state event, or chem-data (ignored on inbound).

| # | File | Content |
|---|------|---------|
| [x] 23.1.1 | `src/backend/main.py` | Build `_base_to_pool_map: dict[str, str]` at startup from `POOL_LIST` (`base -> name`). Replace the two per-pool subscriptions with one `<base>/+` subscribe per pool, and drop `_handle_ble_message` / `_handle_pump_message`. New single handler `_handle_pool_message(client, userdata, msg)` looks up the pool by base prefix, then JSON-content-analyzes the payload: presence of `temp`/`pH`/`cl` → `live_state.push_sample(...)`; presence of `mainPump`/`solarPump` → `live_state.set_pump(...)` (+ `db.insert_pump_event(...)` on change); presence of `chem` data → log + ignore (chem is backend → outbound only). |
| [x] 23.1.2 | `src/backend/main.py` | Pump field names hard-coded as module constants `PUMP_FIELD_MAIN = "mainPump"`, `PUMP_FIELD_SOLAR = "solarPump"`, `PUMP_FIELD_TIME = "time"`. Remove `LIVE_PUMP_FIELD_*` env reads. |
| [x] 23.1.3 | `src/backend/main.py` | Publish topic for measurements becomes `<base>/manual` (was the full topic stored in `POOL_LIST[i].topic`); chemistry publish becomes `<base>/chem`. Both built from the same `POOL_LIST[i].topic` base + a fixed suffix. |
| [x] 23.1.4 | `src/backend/main.py` | `MQTT_KEEPALIVE` moved to the General section (global, single value) — no longer pool-scoped. |

**Verify:** `POOL_LIST=[{"name":"Pool","topic":"pool"}]` makes the backend
subscribe to `pool/+` only; publishing to `pool/ble-yc01`, `pool/pump`, or
any other sub-topic is dispatched by content, not by topic name. Chem-data
payloads on inbound are logged and dropped. Measurement + chemistry POST
endpoints publish to `pool/manual` and `pool/chem` respectively.

### 23.2 Backend: Wildcard dispatch in `mqtt.py`

Goal: Make the MQTT layer explicitly support per-pool wildcard
subscriptions (`+`, `#`) and deliver only matching messages to handlers.

| # | File | Content |
|---|------|---------|
| [x] 23.2.1 | `src/backend/mqtt.py` | Add `_topic_matches(pattern: str, topic: str) -> bool` implementing MQTT wildcard semantics: exact match; `+` matches a single level; `#` matches zero or more trailing levels and must be the last token. Use it in `on_message` to filter incoming messages against all registered `(pattern, handler)` subscriptions, dispatching only on a match. |
| [x] 23.2.2 | `src/backend/mqtt.py` | Keep `subscribe(pattern, on_message)` API: patterns are stored verbatim (including `+` / `#`) and re-subscribed on reconnect. Multiple handlers may register overlapping patterns; first-match-wins dispatch. |
| [x] 23.2.3 | `src/backend/tests/test_mqtt.py` | Wildcard tests: `+` matches one level only (rejects deeper); `#` matches the rest; `#` not at the end is rejected; exact-match still works; non-matching topic is dropped. |

**Verify:** `pytest -v src/backend/tests/test_mqtt.py` green; a publish to
`pool/ble-yc01` is delivered to the pool handler, a publish to
`pool/some/unknown/deeper/topic` matches `#` and is delivered, but a
publish to `other/ble-yc01` is dropped.

### 23.3 Backend: Validations (pool name + base topic, `RESERVED_SUFFIXES`)

Goal: Harden the base-topic model against malformed `POOL_LIST` entries
and topic-injection at the L3 boundary.

| # | File | Content |
|---|------|---------|
| [x] 23.3.1 | `src/backend/main.py` | New `_is_valid_pool_name(name: str) -> bool`: non-empty, length ≤ 50, matches `^[A-Za-z0-9 _.-]+$` (mirrors the FSD/TSD identifier rules). |
| [x] 23.3.2 | `src/backend/main.py` | New `_is_valid_base_topic(topic: str) -> bool`: non-empty, no whitespace, no MQTT wildcards (`+`, `#`), no `$` (system-topic prefix), no leading `/`, no trailing `/`. Rejects anything that could be used to subscribe to unintended topics. |
| [x] 23.3.3 | `src/backend/main.py` | Module constant `RESERVED_SUFFIXES = ("manual", "chem", "pump")`. Pool names are rejected if they equal a reserved suffix (case-insensitive). This guarantees `<base>/manual`, `<base>/chem`, `<base>/pump` are always unambiguous publish/subscribe targets. |
| [x] 23.3.4 | `src/backend/main.py` | `POOL_LIST` parsing: on any invalid entry, log a clear error and **skip** the entry (do not crash startup). The summary log line lists accepted and rejected pools with reasons. |
| [x] 23.3.5 | `src/backend/tests/test_handlers.py` | Rewritten for JSON content analysis: one handler covers BLE + pump payloads; cases: measurement (temp/pH/cl) → `push_sample` called once per metric; pump (mainPump/solarPump) → `set_pump` called with correct field name; chem payload → ignored; unknown payload shape → ignored with warning; handler errors do not break the MQTT loop. |
| [x] 23.3.6 | `src/backend/tests/test_api.py` (or new `test_validators.py`) | Validators: valid pool name passes; empty / too long / special chars rejected; valid base topic passes; base topic with `+`, `#`, `$`, whitespace, leading/trailing `/` rejected; reserved-suffix name rejected. |

**Verify:** `POOL_LIST=[{"name":"manual","topic":"home/x/pool"}]` is rejected
at startup with a clear log line; `POOL_LIST=[{"name":"Pool","topic":"home/
pool/+"}]` is rejected. Valid configs pass through untouched.

### 23.4 mqtt2mail: Single `POOL_LIST` source of truth

Goal: Remove the redundant topic-override env vars
(`MQTT_TOPICS`, `MQTT_ALERT_TOPICS`, `MQTT_AVAILABILITY_TOPICS`,
`MQTT_TOPIC_BASE`). Subscriptions are derived from `POOL_LIST` only.

| # | File | Content |
|---|------|---------|
| [x] 23.4.1 | `src/mqtt2mail/app/mqtt2mail.py` | New `resolve_topics(pool_list: list[dict]) -> dict` returns `{data: [...], alerts: [...], availability: [...]}`. Data topics: each `<base>/+`. Alert topics: each `<base>/+/alert`. Availability: empty list (kept as a key for future use, e.g. `<base>/+/availability`). Wildcard `+` is supported by paho `subscribe`. |
| [x] 23.4.2 | `src/mqtt2mail/app/mqtt2mail.py` | Remove the priority chain `MQTT_TOPICS*` → `POOL_LIST` → `MQTT_TOPIC_BASE`. Only `POOL_LIST` is consulted. Remove the related env reads and fallback logic. |
| [x] 23.4.3 | `src/mqtt2mail/.env.example` | Delete `MQTT_TOPICS`, `MQTT_ALERT_TOPICS`, `MQTT_AVAILABILITY_TOPICS`, `MQTT_TOPIC_BASE`. Document the new contract: "subscriptions are derived from `POOL_LIST` only — one `<base>/+` and one `<base>/+/alert` per pool". |

**Verify:** With `POOL_LIST=[{"name":"Pool","topic":"home/H32/pool"}]`,
mqtt2mail subscribes to `home/H32/pool/+` and `home/H32/pool/+/alert`; an
alert published to `home/H32/pool/pump/alert` is delivered; a message on
`home/other/pool/+` is not.

### 23.5 mqtt-publisher: `POOL_BASE_TOPICS` dict

Goal: Replace the template-based publisher config
(`BLE_TOPIC_TEMPLATE`, `PUMP_TOPIC_TEMPLATE`, `POOLS`) with a clean
`POOL_BASE_TOPICS` dict and hard-coded suffixes.

| # | File | Content |
|---|------|---------|
| [x] 23.5.1 | `src/dev/mqtt-publisher/publisher.py` | New env `POOL_BASE_TOPICS` parsed as a dict `{"<name>": "<base>"}` (e.g. `Pool=home/H32/pool`). Internal `BLE_SUFFIX = "ble-yc01"`, `PUMP_SUFFIX = "pump"` — no env override. Publish functions take a pool name and select the matching base, then build `<base>/ble-yc01` or `<base>/pump`. |
| [x] 23.5.2 | `src/dev/mqtt-publisher/publisher.py` | Remove `BLE_TOPIC_TEMPLATE` and `PUMP_TOPIC_TEMPLATE` env reads. CLI / one-shot publish paths now use the dict. |
| [x] 23.5.3 | `src/dev/mqtt-publisher/tests/test_publisher.py` | Updated for the new dict input: `POOL_BASE_TOPICS={"Pool":"home/H32/pool"}` resolves to `home/H32/pool/ble-yc01` and `home/H32/pool/pump`; unknown pool name is rejected; malformed dict (missing `=`) raises a clear error. |
| [x] 23.5.4 | `src/dev/mqtt-publisher/README.md` | (Updated by parallel sub-agent) Documents the new `POOL_BASE_TOPICS` env format and the fixed suffixes. |

**Verify:** `python publisher.py --pool Pool --kind ble` publishes to
`home/H32/pool/ble-yc01`; `--kind pump` publishes to `home/H32/pool/pump`.
`pytest -v` in the publisher dir is green (11/11).

### 23.6 Infrastructure: docker-compose, .env.example consolidation

Goal: Align the runtime configuration files with the new model. Remove
the working-comment file, drop the override block from mqtt2mail_pool,
and have mqtt-publisher consume `POOL_LIST` instead of its own template
envs.

| # | File | Content |
|---|------|---------|
| [x] 23.6.1 | `src/.env.example` | Consolidated: `POOL_LIST` entries now use the **base** form (e.g. `{"name":"Pool","topic":"home/H32/pool"}`); `MQTT_KEEPALIVE` lives in the General block; old `LIVE_TOPIC_*_TEMPLATE` and `LIVE_PUMP_FIELD_*` lines removed. |
| [x] 23.6.2 | `src/.env.example-comment` | **Deleted** — the long inline working comment was promoted into the real `.env.example` and is no longer needed. |
| [x] 23.6.3 | `src/.env` | Updated structure to match `.env.example`. Local test `POOL_LIST` keeps `topic=pool/manual` for backward compat with existing test data on the broker. |
| [x] 23.6.4 | `src/.env_production` | Updated to the new base-topic format: `POOL_LIST=[{"name":"Pool","topic":"home/H32/pool"}]`. |
| [x] 23.6.5 | `src/docker-compose.yml` | mqtt2mail_pool service: `MQTT_TOPICS`/`MQTT_ALERT_TOPICS`/`MQTT_AVAILABILITY_TOPICS` env override removed — it now reads `POOL_LIST` from the shared `.env` like every other service. |
| [x] 23.6.6 | `src/docker-compose.yml` | mqtt-publisher service: drop `BLE_TOPIC_TEMPLATE` / `PUMP_TOPIC_TEMPLATE` env entries; add `POOL_LIST` so the publisher uses the shared pool config. |

**Verify:** `docker compose config` clean (no warnings about unset
variables, no orphan env entries); `grep -R 'LIVE_TOPIC_\|LIVE_PUMP_FIELD_\|
BLE_TOPIC_TEMPLATE\|PUMP_TOPIC_TEMPLATE' src/` returns zero hits.

### 23.7 Tests (backend 165, frontend 64, publisher 11)

Goal: Keep all three test suites green after the refactor and document
the new totals.

| # | Suite | Result |
|---|-------|--------|
| [x] 23.7.1 | Backend (`src/backend`) | `pytest -v` → **165/165** green (was 132; new: wildcard dispatch, validator cases, content-analysis handler cases, no broken old BLE/pump tests). |
| [x] 23.7.2 | Frontend (`src/frontend`) | `npm run test` → **64/64** green (unchanged from Phase 22; no frontend code touched in this refactor). |
| [x] 23.7.3 | Publisher (`src/dev/mqtt-publisher`) | `pytest -v` → **11/11** green (new dict-based config cases). |

**Verify:** `cd src/backend && pytest -v` → 165 passed, 0 failed.
`cd src/frontend && npm run test` → 64 passed, 0 failed.
`cd src/dev/mqtt-publisher && pytest -v` → 11 passed, 0 failed.


---

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
