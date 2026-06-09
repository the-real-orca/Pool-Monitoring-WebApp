# Reference: Documentation

All project docs live in `docs/` plus the root `README.md` and `AGENTS.md`.

## Document Inventory

| Doc | Purpose | Status |
|-----|---------|--------|
| `docs/Pool-Monitoring - Functional Specification (FSD).md` | What the app does: features, UI wireframes, navigation, API summary, MQTT payloads. Header v2.0. | Mostly current (synced in Phase 27) |
| `docs/Pool-Monitoring - Technical Specification (TSD).md` | How it's built: directory tree, code patterns, component/endpoint contracts, env block, implementation order. Header v2.0. | Mostly current; **MUST consult before coding** |
| `docs/plan.md` | Step-by-step implementation phases (1-28) with checkboxes. Records what is **done**. | Current; update BEFORE committing |
| `docs/Pool-Monitoring - Project Idea.md` | Original concept. | Historical |
| `docs/msg-sample.json` | Sample inbound MQTT sensor payload. | Reference data |
| `docs/pwa-offline-test-plan.md` | Manual PWA/offline test checklist. | Manual QA |
| `docs/Dashboard/*.html` | Static dashboard design mockups (A-F variants + index). Not wired to the app — design exploration only. | Mockups |
| `README.md` | Project intro, features, env, API, structure. | **STALE — see below** |
| `AGENTS.md` | Agent persona, conventions, workflow, testing, modes. | Current (note `AGENTS.md.bak` is an untracked backup) |
| `todo.txt` | Ad-hoc notes (gitignored). | Scratch |
| `log/` | Security reviews + session logs. | Archive |

## Doc Hierarchy / Source of Truth

1. **Code** is authoritative for behaviour.
2. **TSD** for intended structure & patterns (kept in sync via Phase 27).
3. **FSD** for feature intent and UI.
4. **plan.md** for history/status.
5. **README** is the most out-of-date — verify against code before trusting.

## Versioning
- App version is **`2.0`** (`main.py APP_VERSION`, `SettingsPanel.vue`, FSD/TSD
  headers). `frontend/package.json` still says `1.0.0` (bug, F2).

## Key Doc Inconsistencies (verify against code, prefer code)

### README.md is significantly stale (pre-Phase-23/25)
- Line 18-19, 76: documents `POST /api/chem` + `<pool-topic>/chem` →
  **should be** `/api/event` + `<base>/event`.
- Line 61-62: documents `LIVE_TOPIC_BLE_TEMPLATE`/`LIVE_TOPIC_PUMP_TEMPLATE` →
  **removed** in Phase 23 (base-topic model, fixed pump fields).
- Line 56: "default `mosquitto:2883`" — contradicts `.env.example` `MQTT_PORT=1883`.
- Line 108: directory comment "live / form / chemistry / settings" → view is
  `event`, not `chemistry`.

### TSD
- §6 (line ~2134) claims `MQTT_PORT=1883` "matches the dev Mosquitto listener" —
  **wrong**, the bundled broker listens on **2883** (see containerization ref).
- Remaining `/api/chem` mentions are intentional history (404 regression test,
  Phase 25 refactor notes) — correct in context.

### `.env.example`
- Comments at lines 6-9 and 47-51 still say `<base>/chem` / "chemistry
  messages" → should read `/event` (Phase 25/27).

### mqtt2mail README
- Lines 81-100 document removed env vars (`MQTT_TOPICS`, `MQTT_TOPIC_BASE`,
  `MQTT_ALERT_TOPICS`) and a priority chain that no longer exists.

### plan.md vs code
- Phase 23.5 verify steps claim a publisher `--pool/--kind` CLI and a
  `POOL_BASE_TOPICS` env var that were never implemented (env-only, derived
  from `POOL_LIST`). Internally inconsistent with 23.6.6.
- Plan line 51 mentions a `name_alphanumeric` validator; the actual validator is
  `valid_pool_name` (membership in `POOL_NAMES`). Cosmetic.

### Missing artifacts referenced by docs
- TSD §8.2 lists `tests/MeasurementForm.spec.js` — **does not exist**.
- Plan/TSD require `NAME_CONFIG` in `validation.js` — **missing**.

## Conventions for editing docs
- **Update `docs/plan.md` BEFORE committing** code (it records done state).
- When changing the public surface (endpoint, MQTT suffix, enum, env var, view
  state, version), sync **FSD + TSD** in the same change (the Phase 27 pattern).
- Keep doc language German for user-facing descriptions where the rest of the
  doc is German; code identifiers/examples stay as in code.
- Prefer fixing `README.md` to match code rather than the reverse — it is the
  primary onboarding doc and currently the most stale.
