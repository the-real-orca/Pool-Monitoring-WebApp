# Reference: Frontend (Vue 3 PWA)

Location: `src/frontend/`. Vue 3 Composition API (`<script setup>`,
**JavaScript**), Vite 6, Tailwind v4, uPlot, vite-plugin-pwa, Vitest.
Run tests: `cd src/frontend && npm run test` (**94 tests**, 10 spec files).
Build: `npm run build`. Dev: `npm run dev`.

## App shell — `src/App.vue`

- `view = ref('live')` — single source of truth. **No Vue Router.**
  `previousView` remembers where to return from Settings.
- `navigationEntries` (burger menu): `Dashboard`→`live`, `Messungen`→`form`,
  `Ereignisse`→`event`. Settings is a separate menu item.
- Views kept mounted via `v-show` (live/form/event); Settings is `v-if`.
- Toast overlay via `useToast`; click-outside closes the burger menu.

## Components (`src/components/`)

| Component | Notes |
|-----------|-------|
| `LiveView.vue` | Pool selector + live snapshot dashboard + `TrendChart`. Uses `useApi().fetchPoolsLive` + `useLiveData()`. Persists selected pool to localStorage. |
| `MeasurementForm.vue` | Manual measurement form. `FIELD_CONFIG` defaults, `ValueSliderInput` for temp/pH/cl, `ImageCaptureModal` for AI, AI traceability (`aiPH/aiCL/aiImage/aiCorrected`). Fully Germanized. |
| `EventForm.vue` | Event form. 7 UI types (ph split into ph_plus/ph_minus → API `ph` w/ negated amount). `DEFAULT_UNIT` map; uses `utils/eventStep.js` for the amount stepper grid. Collapsible note. |
| `ImageCaptureModal.vue` | Camera/file capture → `compress()` → `analyzeImage()`. Rejects `-1` AI values, emits `applied{pH,cl,image}`. |
| `PumpStatusCard.vue` | Props `pump('main'|'solar')`, `state`, `runningSince`. Shows LÄUFT/AUS/Unbekannt + "läuft seit". |
| `SettingsPanel.vue` | Token field (only setting). `APP_VERSION='2.0'`. Cancel reverts, Save toasts + commits. |
| `ValueSliderInput.vue` | Stepper + popover slider. Props incl. `stepDown` (asymmetric `−` step), `emptyValue`. Hold-to-repeat. v-model. |
| `TrendChart.vue` | 3 uPlot charts (temp/pH/cl), 7-day. Custom wheel/drag pan, pinch, double-tap reset, manual X-sync, lazy backfill (`before_ts`), future-cap (`capSec`). |
| `StepperInput.vue` | **DEAD** — replaced by `ValueSliderInput`; only referenced by its spec. |

## Composables (`src/composables/`)

- **`useApi.js`** — native `fetch`, `authHeaders` Bearer token, hardcoded
  relative `/api/*`. Functions: `fetchPools`, `postMeasurement`,
  `postEvent` (→ `/api/event`), `analyzeImage` (FormData, no Content-Type),
  `fetchPoolsLive`, `fetchLive`, `fetchHistory(pool,metric,days,beforeTs)`,
  `fetchPumpEvents` (**exported/tested but unused in UI**). Error mapping
  401/422/429/code/network.
- **`useSettings.js`** — module `reactive(load())`, deep `watch`→`save`,
  token base64 (`btoa`/`atob`). `DEFAULTS={token:''}` (no `backendUrl`).
- **`useLiveData.js`** — module singleton; `start(pool,{intervalMs=30000})`
  polls `fetchLive`; keeps last snapshot + `usingCached` on failure; `stop()`.
- **`useImage.js`** — `compress(file,{maxEdge,quality})` via
  `createImageBitmap`+`OffscreenCanvas` → JPEG `File`.
- **`useCamera.js`** — `hasCamera` (enumerates videoinput). Used by MeasurementForm.
- **`useToast.js`** — module `reactive` toast; `show(msg,type,duration)`.

## Constants & utils

- **`src/validation.js`** — exports `FIELD_CONFIG` (temp 5-45/0.2/20°C,
  pH 0-14/0.1/7, cl 0-10/0.1/1 mg/l). **`NAME_CONFIG` is MISSING** (plan/TSD
  expect it; name pattern not enforced in frontend).
- **`src/utils/eventStep.js`** — pure helpers `stepFor(unit,value,dir)`,
  `amountDecimals`, `amountEmptyValue`, `snapAmount`. l/kg grid:
  0.1 (<1) / 1 (1-10) / 10 (≥10); asymmetric `−` at thresholds.

## Build / PWA

- **Tailwind v4 CSS-first:** `main.css` = `@import "tailwindcss"` + `@theme {
  --color-primary/success/warning/error }`. No `tailwind.config.js`.
- **vite.config.js:** `vue()`, `tailwindcss()`, `VitePWA(autoUpdate, manifest,
  workbox globPatterns)`. Vitest jsdom + `tests/setup.js`.
- **uPlot** imported per-component in `TrendChart.vue`.
- `Dockerfile` (dev: node build → nginx:1.27-alpine) vs `Dockerfile_production`
  (pre-built `dist/`). `index.html` `lang="de"`.

## Tests (94, 10 specs)
`eventStep`, `validation`, `StepperInput` (dead comp), `ValueSliderInput`,
`LiveView`, `TrendChart` (incl. touch), `useApi`, `useImage`, `useLiveData`,
`useSettings`. `tests/setup.js` stubs matchMedia/canvas/Path2D/ResizeObserver.

## Known Issues
1. **`package.json` version `1.0.0`** — should be `2.0` (UI shows 2.0).
2. **Non-Germanized strings:** `ImageCaptureModal.vue` (errors/loading),
   `EventForm.vue` 401-toast + `SEND`/`Sende...` button.
3. **ASCII umlaut workarounds** (`oeffnen`, `auswaehlen`, `groesser`) in
   `App.vue`/`EventForm.vue` vs proper umlauts elsewhere — standardize.
4. **`PumpStatusCard` seconds-as-minutes bug**: `sinceMinutes` computes seconds
   but labels/splits treat them as minutes.
5. **`NAME_CONFIG` missing** from `validation.js` (and its pattern unenforced).
6. **`tests/useSettings.spec.js`** redefines a local `load/save` with stale
   `backendUrl` instead of importing the real composable.
7. **Dead code:** `StepperInput.vue` (+ spec), `fetchPumpEvents`,
   `LiveView.persistentError`; **missing** `tests/MeasurementForm.spec.js`
   (referenced in TSD §8.2).
8. **38 unhandled uPlot errors** during Vitest (LiveView/TrendChart) — tests
   pass but the run is noisy; investigate teardown/async.
9. **a11y:** icon-only buttons (+/−, eye toggle) lack aria-labels; some
   `<select>`/`datetime` controls under 44px touch target.

## Conventions
- Composables are module-level singletons returning a small API object.
- All user-facing text in **German** (with proper umlauts). Code comments English.
- API calls go through `useApi.js` only; never hardcode fetch elsewhere.
- New components: Composition API `<script setup>`, props validated, `emits`
  declared, touch targets ≥44px.
