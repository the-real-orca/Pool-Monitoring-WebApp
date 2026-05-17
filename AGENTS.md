# AGENTS.md

## Project Overview

Pool-Monitoring PWA – Vue.js 3 (Composition API, JavaScript) frontend + Python/FastAPI backend bridge → MQTT (Mosquitto).
All infrastructure runs in Docker Compose on a vServer with Caddy reverse proxy (Let's Encrypt).

See `docs/plan.md` for full implementation plan with checkboxes.

## Key Directories

- `docs/` – FSD, TSD, plan.md, project idea, sample MQTT message, placeholder icons
- `src/` – app code (see structure below)
    - `backend/` – FastAPI app (`main.py`, `mqtt.py`, `tests/`)
    - `frontend/` – Vue 3 PWA (`src/`, `public/`, `tests/`, Dockerfile, nginx.conf)
    - `docker-compose.yml`, `Caddyfile`, `.env.example`, `.gitignore`

## Documentation

- **FSD:** `docs/Pool-Monitoring - Functional Specification.md` – what the app does
- **TSD:** `docs/Pool-Monitoring - Technical Specification.md` – how it's built (file structure, code patterns, dependencies)
- **Plan:** `docs/plan.md` – step-by-step implementation phases with checkboxes

**Always consult the TSD before writing code.** It contains the exact file layout, code patterns, and design decisions.

## Conventions

- **Interaction language:** German
- **Code comments:** English
- **Git commits:**
    - Concise, imperative (e.g., `feat: add MQTT client`)
    - Append AI agend and model in brackets: `[OpenCode / qwen3.6-plus-free]`
    - Always update `docs/plan.md` BEFORE committing – plan.md reflects what is done, not what will be done
    - Example: `feat: add infrastructure configs (Phase 2) [OpenCode / qwen3.6-plus-free]`

## Architecture Principles

- **Flat and simple:** No unnecessary abstractions, dependencies, or file splits
- **No Vue Router:** 2 views → `ref('form' | 'settings')` in `App.vue`
- **No Pinia:** Composable-level `reactive()` is sufficient
- **No separate config module:** `os.getenv()` directly in `main.py`
- **No Axios:** Native `fetch()` in frontend
- **v1 is stateless:** No database, no dashboard (Future Enhancement)

## Security

- **Warnings:** Fix all warnings seriously, including indirect dependencies
- **Vulnerabilities:** Actively check for open vulnerabilities and bad code practices
- **Issues:** When asked to fix a problem, fix it without argument – even if just a warning
- **Secrets:** Never commit `.env` files, tokens, or credentials

## Testing

- **Backend:** `pytest` in `src/backend/` – run with `cd src/backend && pytest -v`
- **Frontend:** `vitest` in `src/frontend/` – run with `cd src/frontend && npm run test`
- **Linting:** Ruff (backend), ESLint (frontend)

## Startup Protocol

On session start, summarize:

1. Current implementation status (check `docs/plan.md` checkboxes)
2. Previous session changes (check `git log --oneline -5`)
3. Next steps from plan

**Do NOT start implementation without explicit request.**