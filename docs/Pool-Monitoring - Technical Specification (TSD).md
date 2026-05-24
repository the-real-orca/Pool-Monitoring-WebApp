# Technical Specification: Pool-Monitoring PWA

**Version:** 2.0 | **Based on:** FSD 2.0 | **Date:** 2026-05-24

---

## 1. Purpose & Scope

This document describes the concrete technical implementation of FSD v1.0.
Guiding principle: **As flat and simple as possible – as modular as necessary.**
Every file, abstraction, and dependency must justify its place.

**v1 scope:** Measurement form → MQTT publish. No database access, no dashboard.

---

## 2. Technology Stack & Design Decisions

| Area     | Technology | Rationale |
| -------- | ---------- | --------- |
| Frontend | Vue 3 (Composition API), JavaScript | FSD requirement; JS instead of TS avoids tsconfig overhead for a small project |
| Styling  | Tailwind CSS v4 + `@tailwindcss/vite` | Utility-first; v4 needs no `tailwind.config.js` |
| Build    | Vite + `@vitejs/plugin-vue` | Fast, minimally configured |
| PWA      | `vite-plugin-pwa` (Workbox) | Auto-generates service worker + manifest |
| Backend  | Python 3.12, FastAPI | FSD requirement; Pydantic validation included |
| MQTT     | `paho-mqtt ≥ 2.0` | FSD requirement; built-in exponential backoff via `reconnect_delay_set` |
| AI client | `openrouter` (Python SDK) | Official OpenRouter Python SDK – single key, 300+ models, type-safe |
| Multipart | `python-multipart` | Required by FastAPI for `UploadFile` / `Form` parsing |
| Linting  | Ruff + ESLint | Fast, minimal configuration |

**Deliberately excluded:**

| Excluded | Rationale |
| -------- | --------- |
| Vue Router | Only 2 views → `ref('form' \| 'settings')` in `App.vue` suffices |
| Pinia / Vuex | Composable-level `reactive()` is enough for this scope |
| DB / ORM | v1 is stateless; extension prepared in Future Enhancements |
| Separate `config.py` | `os.getenv()` directly in `main.py` – 6 lines instead of a module |
| Axios | Native `fetch()` is sufficient; one less dependency |
| Chart.js | Future Enhancement |
| Separate `middleware/` | FastAPI `Depends()` inline on the route – 5 lines instead of a module |
| Other provider SDKs (`openai`, `anthropic`, `google-genai`) | OpenRouter SDK provides unified access to all of them; no need for per-provider SDKs |
| LangChain / LlamaIndex | Heavy abstractions for a single structured-output call – pure overkill |
| Persistent rate-limit store (Redis) | In-process counter (UTC-day bucket) is sufficient for a single-instance hobby deployment |

---

## 3. Directory Structure

```
src/
├── backend/
│   ├── main.py              # FastAPI app, all routes, Pydantic models, auth, rate-limit
│   ├── mqtt.py              # MQTT client (connect, publish, reconnect)
│   ├── ai.py                # AI client (provider-agnostic, structured output, image storage)
│   ├── requirements.txt
│   ├── pyproject.toml       # Ruff/Black configuration
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.js          # App mount, PWA registration
│   │   ├── App.vue          # Root: view toggle (form|settings), toast display
│   │   ├── validation.js    # Field constants (min, max, step, default, unit)
│   │   ├── components/
│   │   │   ├── StepperInput.vue       # Reusable +/- input stepper
│   │   │   ├── MeasurementForm.vue    # Measurement form with submit flow + photo button
│   │   │   ├── ImageCaptureModal.vue  # Camera capture, compression, preview, AI call
│   │   │   └── SettingsPanel.vue      # Settings (URL, token, name)
│   │   └── composables/
│   │       ├── useApi.js      # fetch wrapper with Bearer auth (incl. analyzeImage)
│   │       ├── useSettings.js # localStorage read/write (reactive)
│   │       ├── useImage.js    # Canvas-based image compression utility
│   │       └── useToast.js    # Toast state (module-level singleton)
│   ├── public/
│   │   └── icons/
│   │       ├── icon-192.png
│   │       └── icon-512.png
│   ├── index.html
│   ├── vite.config.js       # Vite + Vue + Tailwind + PWA
│   ├── nginx.conf           # SPA routing for Nginx
│   └── Dockerfile
├── docker-compose.yml
├── Caddyfile
├── .env.example
└── .gitignore
```

**Test files** live alongside source files:

```
backend/tests/
├── test_models.py
├── test_api.py
├── test_auth.py
└── test_ai.py            # AI client: structured output, refusal, timeout, rate limit

frontend/tests/
├── validation.spec.js
├── useSettings.spec.js
├── StepperInput.spec.js
└── useImage.spec.js      # Image compression: dimensions, MIME, size cap
```

---

## 4. Frontend

### 4.1 View Switching (No Router)

`App.vue` holds `const view = ref('form')` and renders conditionally.
`useToast` is a module-level singleton, callable from any component.

```vue
<!-- App.vue -->
<script setup>
import { ref } from 'vue'
import MeasurementForm from './components/MeasurementForm.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import { useToast } from './composables/useToast.js'

const view = ref('form')
const { toast } = useToast()
</script>

<template>
  <div class="flex min-h-svh items-center justify-center bg-slate-50 p-4">
    <div class="relative w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-lg">
      <div class="bg-primary px-6 py-4 text-center">
        <h1 class="text-2xl font-bold text-white">Pool Monitor</h1>
      </div>
      <div class="p-6">
        <MeasurementForm v-if="view === 'form'" @open-settings="view = 'settings'" />
        <SettingsPanel v-else @close="view = 'form'" />
      </div>
    </div>

    <!-- Global Toast overlay -->
    <Transition name="toast">
      <div v-if="toast.visible" class="fixed bottom-6 left-1/2 ..."
           :class="{ 'bg-success': toast.type === 'success', 'bg-error': toast.type === 'error', 'bg-warning': toast.type === 'warning' }">
        {{ toast.message }}
      </div>
    </Transition>
  </div>
</template>

<style>
.toast-enter-active, .toast-leave-active { transition: opacity 0.3s, transform 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(1rem); }
</style>
```

The app shell provides a centered card layout with a colored header bar. The form title is rendered inside `MeasurementForm.vue` (see FSD wireframe), while the app-level title "Pool Monitor" sits in the header bar.

### 4.2 Components

| File | Responsibility | Props | Emits |
| ---- | -------------- | ----- | ----- |
| `StepperInput.vue` | Number input + +/- stepper, v-model compatible | `modelValue`, `min`, `max`, `step`, `decimals`, `unit` | `update:modelValue` |
| `MeasurementForm.vue` | Form, validation, submit flow, title, settings gear icon, opens `ImageCaptureModal` | – | `open-settings` |
| `ImageCaptureModal.vue` | Camera capture, client-side compression, AI request, result preview | `open` (boolean) | `close`, `applied` (payload `{pH, cl, time}`) |
| `SettingsPanel.vue` | Read/write API token + version display | – | `close` |

**`StepperInput.vue`** – combined number input with +/- stepper buttons:

```vue
<script setup>
import { computed } from 'vue'

const props = defineProps(['modelValue', 'min', 'max', 'step', 'decimals', 'unit'])
const emit = defineEmits(['update:modelValue'])

const inputValue = computed({
  get: () => props.modelValue.toFixed(props.decimals),
  set: (val) => {
    const num = parseFloat(val)
    if (!isNaN(num)) {
      const clamped = Math.max(props.min, Math.min(props.max, num))
      emit('update:modelValue', parseFloat(clamped.toFixed(props.decimals)))
    }
  },
})

function step(dir) {
  const next = parseFloat((props.modelValue + dir * props.step).toFixed(props.decimals))
  if (next >= props.min && next <= props.max) emit('update:modelValue', next)
}
</script>

<template>
  <div class="flex items-center gap-2">
    <button @click="step(-1)" :disabled="modelValue <= min">−</button>
    <input v-model.number="inputValue" type="number" :step="step" :min="min" :max="max" />
    <span>{{ unit }}</span>
    <button @click="step(+1)" :disabled="modelValue >= max">+</button>
  </div>
</template>
```

The component provides both direct value entry via a number input and touch-friendly incremental adjustment via stepper buttons. The input is clamped to min/max bounds and formatted to the specified decimal places.

**`MeasurementForm.vue`** – contains the full submit flow:

```js
// Internal flow in MeasurementForm.vue (setup)
const { settings } = useSettings()
const { postMeasurement, loading, error } = useApi()
const { show: showToast } = useToast()

// Local form state (reactive, no store)
const form = reactive({
  time: '',         // datetime-local string, initialized to local now
  name: '',         // populated from fetchPools
  temp: FIELD_CONFIG.temp.default,
  pH:   FIELD_CONFIG.pH.default,
  cl:   FIELD_CONFIG.cl.default,
  notes: '',        // optional text
})

const errors = reactive({})   // inline validation errors

function validate() {
  // clears errors, checks name (1-50 chars, alphanumeric + spaces) and time
  // returns true if valid
}

async function submit() {
  if (!validate()) return
  const timestamp = Math.floor(new Date(form.time).getTime() / 1000)
  const ok = await postMeasurement({ ...form, time: timestamp })
  if (ok) {
    showToast('Measurement saved', 'success')
    resetForm()
  } else if (error.value === '401') {
    showToast('Unauthorized – check your token in settings', 'error')
  } else {
    showToast('Failed to send measurement', 'error')
  }
}
```

The form title ("Measurements") is rendered inside `MeasurementForm.vue` (matching the FSD wireframe), not in `App.vue`.

**`SettingsPanel.vue`** – no own state, all fields bound directly to `settings`:

```vue
<script setup>
import { useSettings } from '../composables/useSettings.js'
const { settings } = useSettings()
const emit = defineEmits(['close'])
const APP_VERSION = '2.0.0'
</script>

<template>
  <div class="relative space-y-5">
    <button @click="emit('close')" class="...">✕</button>
    <h1 class="text-center text-2xl font-bold">Settings</h1>
    <input v-model="settings.token" type="password" placeholder="Bearer token" />
    <p class="text-center text-xs text-slate-400">Version {{ APP_VERSION }}</p>
  </div>
</template>
```

### 4.3 Composables

#### `useSettings.js`

Module-level `reactive` object – initialized once, shared by all components.
`watch` writes to localStorage on every change.
Token is stored Base64-encoded (obfuscation, not a security feature).

```js
import { reactive, watch } from 'vue'

const KEY = 'pool_monitor_settings'
const DEFAULTS = { backendUrl: '/api', token: '' }

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? '{}')
    return { ...DEFAULTS, ...raw, token: raw.token ? atob(raw.token) : '' }
  } catch { return { ...DEFAULTS } }
}

function save(s) {
  localStorage.setItem(KEY, JSON.stringify({ ...s, token: btoa(s.token) }))
}

// Module-level singleton – created only once
const settings = reactive(load())
watch(settings, save, { deep: true })

export function useSettings() {
  return { settings }
}
```

#### `useApi.js`

Reads `settings.backendUrl` and `settings.token`.
Returns a local `{ loading, error }` per call (no global loading state).
No automatic retry – the user has a retry button (FSD 7.1).

```js
import { ref } from 'vue'
import { useSettings } from './useSettings.js'

export function useApi() {
  const { settings } = useSettings()
  const loading = ref(false)
  const error = ref(null)

  async function fetchPools() {
    // GET /api/pools and return the array, handle errors
  }

  async function postMeasurement(form) {
    loading.value = true
    error.value = null
    const payload = {
      time:       Math.floor(Date.now() / 1000),
      name:       form.name,
      sensorType: 'manual',
      pH:         form.pH,
      cl:         form.cl,
      temp:       form.temp,
      notes:      form.notes || null,
    }
    try {
      const res = await fetch(`${settings.backendUrl}/measurements`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${settings.token}`,
        },
        body: JSON.stringify(payload),
      })
      if (res.status === 401) { error.value = '401'; return false }
      if (!res.ok) { error.value = String(res.status); return false }
      return true
    } catch {
      error.value = 'network'
      return false
    } finally {
      loading.value = false
    }
  }

  return { loading, error, postMeasurement }
}
```

#### `useToast.js`

Module-level singleton. `show()` is callable from any component without props/events.
`toast` is only rendered in `App.vue`.

```js
import { reactive } from 'vue'

const toast = reactive({ message: '', type: 'success', visible: false })
let _timer = null

export function useToast() {
  function show(message, type = 'success', duration = 3000) {
    clearTimeout(_timer)
    Object.assign(toast, { message, type, visible: true })
    _timer = setTimeout(() => { toast.visible = false }, duration)
  }
  return { toast, show }
}
```

### 4.4 Validation Constants (`validation.js`)

Central source for all field boundaries. Used by `MeasurementForm.vue` and `StepperInput.vue`.
Backend validation (Pydantic `Field()`) uses the same values.

```js
export const FIELD_CONFIG = {
  temp: { min: 5.0,  max: 45.0,  step: 0.2, default: 20.0, decimals: 1, unit: '°C'   },
  pH:   { min: 0.0,  max: 14.0,  step: 0.1, default: 7.0,  decimals: 1, unit: ''     },
  cl:   { min: 0.0,  max: 10.0,  step: 0.1, default: 1.0,  decimals: 1, unit: 'mg/l' },
}

export const NAME_CONFIG = { minLength: 1, maxLength: 50, pattern: /^[a-zA-Z0-9 ]+$/ }
```

### 4.5 Build Configuration (`vite.config.js`)

`vite-plugin-pwa` generates the service worker (Workbox, `CacheFirst` for static assets)
and `manifest.json` automatically from the configuration.

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Pool Monitor',
        short_name: 'Pool',
        theme_color: '#0EA5E9',
        background_color: '#F8FAFC',
        display: 'standalone',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,png,svg}'],
        runtimeCaching: [], // v1: app shell only, no API caching
      },
    }),
  ],
})
```

Tailwind CSS v4: no `tailwind.config.js` needed. Only configuration in `src/main.css`:

```css
@import "tailwindcss";

@theme {
  --color-primary: #0EA5E9;
  --color-success: #22C55E;
  --color-warning: #F59E0B;
  --color-error:   #EF4444;
}
```

### 4.6 Frontend Dependencies (`package.json`)

```json
{
  "dependencies": {
    "vue": "^3.5"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5",
    "@tailwindcss/vite": "^4",
    "tailwindcss": "^4",
    "vite": "^6",
    "vite-plugin-pwa": "^0.21",
    "vitest": "^2",
    "@vue/test-utils": "^2",
    "jsdom": "^25"
  }
}
```

`jsdom` is required for `vitest` to run component tests in a simulated DOM environment (`environment: 'jsdom'` in `vite.config.js`).

### 4.7 Image Capture & Analysis Flow

The image-analysis feature lives in **`ImageCaptureModal.vue`** and the
**`useImage`** composable. `MeasurementForm.vue` only renders a button and the modal:

```js
// Inside MeasurementForm.vue (setup)
const showCapture = ref(false)

function applyAnalysis({ pH, cl, time }) {
  if (pH != null) form.pH = pH
  if (cl != null) form.cl = cl
  if (time != null) form.time = new Date(time * 1000).toISOString().slice(0, 16)
  showCapture.value = false
  showToast('Values extracted – please verify', 'success')
}
```

**`ImageCaptureModal.vue`** orchestrates capture → compress → upload:

```vue
<script setup>
import { ref } from 'vue'
import { useApi } from '../composables/useApi.js'
import { useImage } from '../composables/useImage.js'

const props = defineProps({ open: Boolean })
const emit = defineEmits(['close', 'applied'])

const { analyzeImage, loading, error } = useApi()
const { compress } = useImage()
const fileRef = ref(null)
const previewUrl = ref(null)

async function onFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const compressed = await compress(file, { maxEdge: 1600, quality: 0.85 })
  previewUrl.value = URL.createObjectURL(compressed)
  const result = await analyzeImage(compressed)
  if (result) emit('applied', result)
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 ...">
    <input ref="fileRef" type="file" accept="image/*" capture="environment"
           class="hidden" @change="onFileSelected" />
    <button @click="fileRef.click()" :disabled="loading">Take photo</button>
    <img v-if="previewUrl" :src="previewUrl" />
    <p v-if="loading">Analyzing…</p>
    <p v-if="error" class="text-error">{{ error }}</p>
    <button @click="emit('close')">Cancel</button>
  </div>
</template>
```

Key points:

- `<input type="file" accept="image/*" capture="environment">` opens the rear camera on
  mobile while gracefully degrading to a file picker on desktop.
- Compression happens on the **client** (Canvas API) – upload payload stays < 2 MB.
- The modal does **not** mutate form state directly; it only emits `applied` with the
  values, and the parent merges them. This keeps the form the single source of truth.

### 4.8 `useImage.js` – Compression Helper

```js
export function useImage() {
  async function compress(file, { maxEdge = 1600, quality = 0.85 } = {}) {
    const bmp = await createImageBitmap(file)
    const scale = Math.min(1, maxEdge / Math.max(bmp.width, bmp.height))
    const w = Math.round(bmp.width * scale)
    const h = Math.round(bmp.height * scale)
    const canvas = new OffscreenCanvas(w, h)
    canvas.getContext('2d').drawImage(bmp, 0, 0, w, h)
    const blob = await canvas.convertToBlob({ type: 'image/jpeg', quality })
    return new File([blob], 'capture.jpg', { type: 'image/jpeg' })
  }
  return { compress }
}
```

`OffscreenCanvas` is supported on all modern target browsers (FSD 3.6). A `<canvas>`
fallback can be added if iOS Safari < 17 needs to be supported.

### 4.9 `useApi.analyzeImage`

Extends the existing composable. Uses `multipart/form-data` so binary data is not
Base64-bloated (see `Integration multimodaler KI-Agenten.md` §1):

```js
async function analyzeImage(file) {
  loading.value = true; error.value = null
  const fd = new FormData()
  fd.append('image', file)
  fd.append('data', JSON.stringify({ hint: 'pool test strip' }))
  try {
    const res = await fetch(`${settings.backendUrl}/analyze-image`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${settings.token}` }, // no Content-Type!
      body: fd,
    })
    if (res.status === 401) { error.value = 'Unauthorized – check token'; return null }
    if (res.status === 429) { error.value = 'Daily limit reached';        return null }
    if (res.status === 422) { error.value = 'AI could not analyze image'; return null }
    if (!res.ok)            { error.value = `AI service error (${res.status})`; return null }
    return await res.json()
  } catch {
    error.value = 'Network error'
    return null
  } finally {
    loading.value = false
  }
}
```

> Critical: do **not** set `Content-Type` manually – the browser must add the multipart
> boundary itself. Setting it breaks `python-multipart` parsing in FastAPI.

---

## 5. Backend

### 5.1 File Structure and Split

`main.py` contains everything that does not need its own state: configuration, Pydantic
models, auth dependency, app lifespan, rate-limit counter, and all routes.
`mqtt.py` is separated because the client manages its own threading state (`loop_start()`).
`ai.py` is separated because it owns the provider abstraction, prompt construction, and
on-disk image/result persistence.

```
main.py
 ├── Imports
 ├── Configuration (os.getenv)
 ├── Pydantic models: Measurement, ImageAnalysisResult
 ├── Auth dependency: verify_token()
 ├── Rate-limit counter (UTC-day bucket, in-process)
 ├── App + Lifespan (MQTT connect/disconnect, AI client lifecycle)
 ├── POST /api/measurements
 ├── POST /api/analyze-image
 └── GET  /api/status
```

### 5.2 Configuration

Directly via `os.getenv()` – no separate config module:

```python
import os, time, secrets as _secrets
from contextlib import asynccontextmanager

import json

API_TOKEN   = os.getenv("API_TOKEN", "")
MQTT_HOST   = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", "2883"))
MQTT_USER   = os.getenv("MQTT_USER", "")
MQTT_PASS   = os.getenv("MQTT_PASS", "")
POOL_LIST   = json.loads(os.getenv("POOL_LIST", '[{"name": "Pool", "topic": "pool/manual"}]'))

# AI image analysis
AI_PROVIDER             = os.getenv("AI_PROVIDER", "openai")
AI_API_KEY              = os.getenv("AI_API_KEY", "")
AI_MODEL                = os.getenv("AI_MODEL", "openai/gpt-4o")
AI_MAX_REQUESTS_PER_DAY = int(os.getenv("AI_MAX_REQUESTS_PER_DAY", "10"))
AI_TIMEOUT_SECONDS      = int(os.getenv("AI_TIMEOUT_SECONDS", "30"))
AI_IMAGE_STORAGE_PATH   = os.getenv("AI_IMAGE_STORAGE_PATH", "/data/ai")
AI_IMAGE_RETENTION_DAYS = int(os.getenv("AI_IMAGE_RETENTION_DAYS", "30"))
AI_MAX_IMAGE_BYTES      = int(os.getenv("AI_MAX_IMAGE_BYTES", str(10 * 1024 * 1024)))

APP_VERSION = "2.0.0"
_start_time = time.time()
```

### 5.3 Pydantic Model & Validation

Validation ranges exactly match the `FIELD_CONFIG` values from `validation.js`.
The `status` key from `msg-sample.json` is set server-side – it is not an API input.

```python
from pydantic import BaseModel, Field, field_validator
import re

class Measurement(BaseModel):
    time:       int
    name:       str  = Field(min_length=1, max_length=50)
    sensorType: str  = "manual"
    pH:         float = Field(ge=0.0, le=14.0)
    cl:         float = Field(ge=0.0, le=10.0)
    temp:       float = Field(ge=5.0, le=45.0)
    notes:      str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def valid_pool_name(cls, v: str) -> str:
        valid_names = [pool["name"] for pool in POOL_LIST]
        if v not in valid_names:
            raise ValueError(f"Unknown pool name: {v}")
        return v

    @field_validator("pH", "cl", "temp")
    @classmethod
    def one_decimal(cls, v: float) -> float:
        return round(v, 1)
```

**MQTT payload:** On publish, a new sanitized message is built – no passthrough of raw data.

```python
def build_mqtt_payload(m: Measurement) -> tuple[str, dict]:
    topic = next((pool["topic"] for pool in POOL_LIST if pool["name"] == m.name), "pool/manual")
    payload = {
        "time":       m.time,
        "name":       m.name,
        "sensorType": m.sensorType,
        "temp":       m.temp,
        "pH":         m.pH,
        "cl":         m.cl,
    }
    if m.notes:
        payload["notes"] = m.notes
    return topic, payload
```

### 5.4 Auth Dependency

`secrets.compare_digest` instead of `==` prevents timing attacks:

```python
from fastapi import Header, HTTPException, Depends
import secrets as _secrets

async def verify_token(authorization: str = Header(alias="Authorization")):
    expected = f"Bearer {API_TOKEN}"
    if not API_TOKEN or not _secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")
```

Bound directly on the route via `dependencies=[Depends(verify_token)]`.

### 5.5 Routes & Lifespan

```python
from fastapi import FastAPI, HTTPException, Depends
import mqtt  # mqtt.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt.connect(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS)
    await ai.startup()       # creates AI_IMAGE_STORAGE_PATH, opens OpenRouter SDK client
    yield
    await ai.shutdown()
    mqtt.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/api/pools", dependencies=[Depends(verify_token)])
async def get_pools():
    return [{"name": pool["name"]} for pool in POOL_LIST]

@app.post("/api/measurements", status_code=201,
          dependencies=[Depends(verify_token)])
async def post_measurement(m: Measurement):
    topic, payload = build_mqtt_payload(m)
    if not mqtt.publish(topic, payload):
        raise HTTPException(status_code=503, detail="MQTT unavailable")
    return {"status": "success", "message": "Measurement published to MQTT"}

@app.get("/api/status")
async def get_status():
    return {
        "status":                     "healthy",
        "mqttConnected":              mqtt.is_connected(),
        "aiConfigured":               bool(AI_API_KEY),
        "imageAnalysisRequestsToday": _ai_counter["count"],
        "uptime":                     int(time.time() - _start_time),
        "version":                    APP_VERSION,
    }
```

### 5.6 `mqtt.py` – MQTT Client

Own file due to own threading state (`loop_start()`).
`reconnect_delay_set(min_delay=1, max_delay=300)` activates paho-internal exponential backoff.

```python
import json
import logging
import paho.mqtt.client as mqtt_lib

_client: mqtt_lib.Client | None = None

def connect(host: str, port: int, user: str, password: str) -> None:
    global _client
    _client = mqtt_lib.Client(mqtt_lib.CallbackAPIVersion.VERSION2)
    if user:
        _client.username_pw_set(user, password)
    _client.reconnect_delay_set(min_delay=1, max_delay=300)
    _client.on_connect = lambda c, u, d, rc, p: (
        logging.info("MQTT connected (rc=%s)", rc) if rc == 0 else logging.error("MQTT connection failed (rc=%s)", rc)
    )
    _client.on_disconnect = lambda c, u, d, rc, p: (
        logging.warning("MQTT disconnected (rc=%s), reconnecting...", rc)
    )
    _client.connect_async(host, port)
    _client.loop_start()
    logging.info("MQTT connecting to %s:%s", host, port)

def publish(topic: str, payload: dict) -> bool:
    if not is_connected():
        return False
    result = _client.publish(topic, json.dumps(payload), qos=1)
    return result.rc == mqtt_lib.MQTT_ERR_SUCCESS

def disconnect() -> None:
    if _client:
        _client.loop_stop()
        _client.disconnect()

def is_connected() -> bool:
    return _client is not None and _client.is_connected()
```

`connect_async()` is used instead of `connect()` to avoid blocking during startup. The `on_connect` callback logs connection success or failure, complementing the existing `on_disconnect` handler.

### 5.7 `ai.py` – Multimodal AI Client

Uses the official **`openrouter` Python SDK** (`pip install openrouter`). A single
SDK instance (initialized in `startup()`) gives typed access to any of the 300+
models in the OpenRouter catalog – OpenAI GPT-4o, Anthropic Claude, Google Gemini,
Mistral, Aleph Alpha Pharia, and more – via one API key.

**Pydantic result model** – consumed by both `ai.py` and the route handler:

```python
from pydantic import BaseModel, Field

class ImageAnalysisResult(BaseModel):
    pH:         float | None = Field(default=None, ge=0.0, le=14.0)
    cl:         float | None = Field(default=None, ge=0.0, le=10.0)
    time:       int   | None = None     # Unix timestamp if visible on the strip / clock
    confidence: float        = Field(default=0.0, ge=0.0, le=1.0)
    model:      str
```

**SDK client lifecycle** (`startup()` / `shutdown()`):

```python
import openrouter

_client: openrouter.OpenRouter | None = None

async def startup() -> None:
    global _client
    _client = openrouter.OpenRouter(
        api_key=AI_API_KEY,
        timeout=AI_TIMEOUT_SECONDS,
        http_referer=FRONTEND_URL or "https://pool-monitor.local",
        x_open_router_title="PoolMonitor/2.0",
    )
    os.makedirs(AI_IMAGE_STORAGE_PATH, exist_ok=True)
    _prune_old_images()

async def shutdown() -> None:
    global _client
    _client = None   # context manager handles close
```

**Image sending** – the OpenRouter multimodal API accepts images as URL objects or
as base64-encoded data URIs inline in the message content:

```python
import base64, hashlib

def _image_content(image_bytes: bytes, mime: str) -> list[dict]:
    b64 = base64.b64encode(image_bytes).decode()
    return [
        {"type": "text", "text": SYSTEM_PROMPT},
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"},
        },
    ]

SYSTEM_PROMPT = (
    "You analyze a photo of a pool test strip held next to its reference color scale. "
    "Return ONLY JSON matching the provided schema. Compare the strip's color fields "
    "against the reference scale visible in the same image. Account for outdoor lighting "
    "and reflections; if uncertain about a value, return null instead of guessing. "
    "Never hallucinate values that you cannot see clearly."
)
```

**Structured output** – the OpenRouter SDK extends the OpenAI `response_format`
mechanism. The schema is passed as a Pydantic model to `response_format`;
the SDK handles serialization and the provider returns guaranteed-JSON:

```python
async def analyze_pool_image(image_bytes: bytes, mime: str,
                             hint: dict | None = None) -> ImageAnalysisResult:

    assert _client is not None, "startup() not called"

    content = _image_content(image_bytes, mime)
    if hint:
        content.insert(0, {"type": "text", "text": f"Context: {hint.get('hint','')}"})

    raw = _client.chat.send(
        messages=[{"role": "user", "content": content}],
        model=AI_MODEL,
        response_format=ImageAnalysisResult,   # Pydantic model → JSON schema
        # provider: {"sort": "price"}  # optional: let OpenRouter pick cheapest suitable model
    )

    # raw is a full OpenAI-compatible response object
    msg = raw.choices[0].message

    # Refusal check (OpenAI-compatible)
    if getattr(msg, "refusal", None):
        raise AIRefusalError(msg.refusal)

    parsed = msg.parsed          # typed Pydantic model when response_format is set
    return ImageAnalysisResult(
        pH=parsed.pH, cl=parsed.cl, time=parsed.time,
        confidence=getattr(parsed, "confidence", 0.0),
        model=raw.model or AI_MODEL,
    )
```

**Error taxonomy** – the SDK raises provider/HTTP exceptions that are caught and
re-mapped to application-level errors:

| Exception           | HTTP | Trigger                                                            |
| ------------------- | ---- | ------------------------------------------------------------------ |
| `AIRefusalError`    | 422  | `msg.refusal` is non-empty (OpenAI-compatible refusal marker)     |
| `AISchemaError`     | 502  | `msg.parsed` raises `ValidationError` or raw is not JSON           |
| `AIAuthError`       | 502  | SDK raises `AuthenticationError` (401/403 from provider)          |
| `AITimeoutError`    | 503  | SDK raises `TimeoutError` or request exceeds `AI_TIMEOUT_SECONDS` |
| `AIServiceError`    | 503  | SDK raises `RateLimitError` (429) or other 5xx from provider      |

> **SDK note:** `openrouter` is in beta; pin the package version in `requirements.txt`
> to avoid unexpected breaking changes (e.g. `openrouter>=0.9,<1.0`).

**Image persistence** – on every `/api/analyze-image` call:

```
$AI_IMAGE_STORAGE_PATH/
└── 2026-05-24/
    ├── 20260524T143012Z_<sha256[:12]>.jpg     # original (post-compression) image
    └── 20260524T143012Z_<sha256[:12]>.json    # request meta + AI raw + parsed result
```

A startup task prunes directories older than `AI_IMAGE_RETENTION_DAYS`.
SHA256 prefix in the filename allows cheap deduplication without a database.

**Public API of `ai.py`:**

```python
async def analyze_pool_image(image_bytes: bytes, mime: str,
                             hint: dict | None = None) -> ImageAnalysisResult: ...

async def startup() -> None: ...   # creates AI_IMAGE_STORAGE_PATH, starts OpenRouter client
async def shutdown() -> None: ...  # closes client (context manager)

### 5.8 Rate Limiting for `/api/analyze-image`

In addition to the global Phase-14 rate limiter (per-IP, sliding window on `/api/*`),
image analysis has a stricter **per-day cap** to bound AI costs and abuse. It is a
simple in-process counter keyed by the current UTC date – no Redis, no DB:

```python
from datetime import datetime, timezone

_ai_counter = {"date": "", "count": 0}

def ai_rate_check_and_increment() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _ai_counter["date"] != today:
        _ai_counter.update(date=today, count=0)
    if _ai_counter["count"] >= AI_MAX_REQUESTS_PER_DAY:
        raise HTTPException(status_code=429, detail="Daily image-analysis limit reached")
    _ai_counter["count"] += 1
    return AI_MAX_REQUESTS_PER_DAY - _ai_counter["count"]
```

Limitations (acceptable for a single-instance hobby deployment):

- Counter resets on container restart – an attacker can re-burst once per restart.
  Mitigated by the existing per-IP sliding-window limiter from Phase 14.
- Not shared across replicas. A future migration to Redis is straightforward.

### 5.9 `POST /api/analyze-image` Route

```python
from fastapi import File, Form, UploadFile
from pydantic import Json, BaseModel

class AnalyzeImageHint(BaseModel):
    hint: str | None = None

@app.post("/api/analyze-image",
          dependencies=[Depends(verify_token)],
          response_model=ImageAnalysisResult)
async def analyze_image_endpoint(
    image: UploadFile = File(...),
    data:  Json[AnalyzeImageHint] = Form(default=AnalyzeImageHint()),
):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(400, "Only JPEG or PNG accepted")
    raw = await image.read()
    if len(raw) > AI_MAX_IMAGE_BYTES:
        raise HTTPException(400, "Image too large")

    remaining = ai_rate_check_and_increment()

    try:
        result = await ai.analyze_pool_image(raw, image.content_type, data.model_dump())
    except ai.AIRefusalError:    raise HTTPException(422, "AI refused to analyze")
    except ai.AISchemaError:     raise HTTPException(502, "AI returned invalid schema")
    except ai.AIAuthError:       raise HTTPException(502, "AI authentication failed")
    except ai.AITimeoutError:    raise HTTPException(503, "AI service timeout")
    except ai.AIServiceError:    raise HTTPException(503, "AI service unavailable")

    response = result.model_dump()
    response["requestsRemainingToday"] = remaining
    return response
```

Notes:

- `pydantic.Json[AnalyzeImageHint]` parses the `data` form field as JSON
  (see `Integration multimodaler KI-Agenten.md` §2 – this is the "magic link").
- `image.content_type` and explicit byte-size check defend against oversized uploads
  before any AI cost is incurred.
- The token check (`verify_token`) is applied **before** the file is read, so
  unauthenticated callers cannot consume bandwidth or daily quota.

### 5.10 Backend Dependencies (`requirements.txt`)

```
fastapi>=0.115
uvicorn[standard]>=0.30
paho-mqtt>=2.0
python-dotenv>=1.0
python-multipart>=0.0.9
openrouter>=0.9,<1.0    # Official OpenRouter Python SDK (beta – pin major version)
httpx>=0.27             # Test transport (TestClient) + SDK internals; not used directly in app code
pytest>=8.0
pytest-asyncio>=0.23
```

`python-multipart` is required by FastAPI's `UploadFile` / `Form`. The OpenRouter SDK is
pinned to `>=0.9,<1.0` because it is in beta – this prevents unexpected breaking changes
after a minor version bump. `httpx` remains for the test transport (`TestClient`). `pytest-asyncio` enables
testing the async AI client without a real provider.

---

## 6. Infrastructure

### 6.1 Docker Compose

Four services: `frontend`, `backend`, `caddy`, `mosquitto`.
Mosquitto is included as a **dev-only** service for local testing. In production, an existing external Mosquitto instance is used – set `MQTT_HOST` in `.env` accordingly and remove the `mosquitto` service.

The Mosquitto container uses port **2883** (host) → **2883** (container) to avoid collisions with any Mosquitto instance that may already run on the host system.

```yaml
services:
  frontend:
    build: ./frontend
    restart: unless-stopped

  backend:
    build: ./backend
    restart: unless-stopped
    env_file: .env
    depends_on:
      - mosquitto

  mosquitto:
    image: eclipse-mosquitto:2
    restart: unless-stopped
    ports:
      - "2883:2883"
    volumes:
      - ./mosquitto/config:/mosquitto/config:ro

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
    depends_on: [frontend, backend]

volumes:
  caddy_data:
```

### 6.2 Dockerfiles

**Backend** – slim image, no build stage needed:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend** – Multi-stage: Build (Node) + Serve (Nginx):

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

`nginx.conf` – SPA routing + static asset caching:

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static assets: long-lived cache
    location ~* \.(js|css|png|svg|woff2|webmanifest)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 6.3 Caddyfile

Production (`pool.io10.org`):

```
pool.io10.org {
    handle /api/* {
        reverse_proxy backend:8000
    }
    handle {
        reverse_proxy frontend:80
    }
}
```

Dev (local testing, `:80`):

```
:80 {
    handle /api/* {
        reverse_proxy backend:8000
    }
    handle {
        reverse_proxy frontend:80
    }
}
```

Caddy automatically obtains and renews a Let's Encrypt certificate for `pool.io10.org`. The dev config uses `:80` without TLS for local testing.

### 6.4 `.env.example`

```env
API_TOKEN=change-me-to-a-secure-random-token
MQTT_HOST=mosquitto
MQTT_PORT=2883
MQTT_USER=
MQTT_PASS=
MQTT_TOPIC=pool/manual
FRONTEND_URL=https://pool.io10.org

# AI image analysis (optional – feature is disabled when AI_API_KEY is empty)
# openrouter is the preferred default; it provides a unified API to models from
# OpenAI, Anthropic, Google, Mistral, Aleph Alpha and others via a single key.
AI_PROVIDER=openrouter
AI_API_KEY=
AI_MODEL=openai/gpt-4o
AI_MAX_REQUESTS_PER_DAY=10
AI_TIMEOUT_SECONDS=30
AI_IMAGE_STORAGE_PATH=/data/ai
AI_IMAGE_RETENTION_DAYS=30
AI_MAX_IMAGE_BYTES=10485760
```

**Note:** `MQTT_PORT=2883` matches the dev Mosquitto listener. For production with an external broker, change `MQTT_HOST` to the external address and `MQTT_PORT` to the broker's port (typically `1883`).
`FRONTEND_URL` is used by the backend CORS middleware – set to the production domain.

---

## 7. Security

| Measure | Implementation |
| ------- | -------------- |
| HTTPS / HSTS | Caddy + Let's Encrypt, automatic |
| Token comparison | `secrets.compare_digest()` (prevents timing attacks) |
| Input sanitization | Pydantic validation; backend builds new payload (no passthrough) |
| Token frontend | Base64 in localStorage (obfuscation, not cryptographic protection) |
| CORS | FastAPI `CORSMiddleware`, own domain only, `allow_origins=[FRONTEND_URL]` |
| MQTT auth | Username/password, backend-internal, never exposed to frontend |
| MQTT QoS | QoS 1 (at least once) for publish |
| AI API key | Server-side env var only, **never** sent to or referenced from the frontend |
| Image upload | MIME allow-list (`image/jpeg`, `image/png`), hard byte cap, auth before read |
| AI rate limit | Per-day counter (`AI_MAX_REQUESTS_PER_DAY`) returns HTTP 429 before AI call |
| AI logging | Persisted images + raw responses are written to a non-public path inside the container; rotated by `AI_IMAGE_RETENTION_DAYS` |
| AI output validation | Provider response parsed via Pydantic with field bounds; invalid → HTTP 502 (no passthrough) |

---

## 8. Testing

### 8.1 Backend (`pytest` + `httpx`)

```
backend/tests/
├── test_models.py   # Pydantic: valid values, boundaries, invalid values, rounding
├── test_api.py      # HTTP endpoints via TestClient (MQTT + AI mocked)
├── test_auth.py     # verify_token: valid, missing, wrong
└── test_ai.py       # ai.analyze_pool_image: structured-output happy path,
                     #   refusal -> AIRefusalError, schema mismatch -> AISchemaError,
                     #   timeout -> AITimeoutError, rate-limit counter rollover
```

Base fixture in `conftest.py`:

```python
import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ["API_TOKEN"] = "test-token"


@pytest.fixture
def client():
    if "main" in sys.modules:
        del sys.modules["main"]
    with patch("mqtt.publish", return_value=True), \
         patch("mqtt.is_connected", return_value=True):
        from main import app
        yield TestClient(app)
```

`API_TOKEN` is set via environment variable so the auth dependency works in tests. `sys.modules["main"]` is cleared between test runs to avoid stale module state.

### 8.2 Frontend (`vitest` + `@vue/test-utils`)

```
frontend/tests/
├── validation.spec.js      # FIELD_CONFIG boundaries and NAME_CONFIG pattern
├── useSettings.spec.js     # localStorage read/write, defaults, token encoding
├── StepperInput.spec.js    # Stepper logic: steps, min/max boundaries, emit
└── useImage.spec.js        # Compression: max edge clamp, JPEG output, byte cap
```

---

## 9. Implementation Order

| # | Step | Artifacts |
|---|------|-----------|
| 1 | Project structure + config files | `.env.example`, `.gitignore` |
| 2 | Infrastructure | `docker-compose.yml`, `Caddyfile`, both `Dockerfile`, `nginx.conf` |
| 3 | Backend: MQTT client | `mqtt.py` |
| 4 | Backend: App + Routes | `main.py` |
| 5 | Backend tests | `tests/test_*.py` |
| 6 | Frontend: Constants + Composables | `validation.js`, `useSettings.js`, `useApi.js`, `useToast.js` |
| 7 | Frontend: Components | `StepperInput.vue`, `MeasurementForm.vue`, `SettingsPanel.vue` |
| 8 | Frontend: App shell + PWA | `App.vue`, `main.js`, `vite.config.js`, icons |
| 9 | Frontend tests | `tests/*.spec.js` |
| 10 | Integration | `docker compose up` end-to-end verification |
| 11 | Backend: AI client | `ai.py`, AI env vars, rate-limit counter |
| 12 | Backend: `/api/analyze-image` route + tests | `main.py`, `tests/test_ai.py` |
| 13 | Frontend: Image capture flow | `useImage.js`, `ImageCaptureModal.vue`, `useApi.analyzeImage`, button in `MeasurementForm.vue` |
| 14 | Frontend tests | `tests/useImage.spec.js` |
| 15 | Integration | End-to-end photo capture → AI → form prefill |
