# Projektanalyse: Pool-Monitoring PWA

**Datum:** 2026-06-09
**Test-Status:** Backend `pytest` 185/185 ✓ | Frontend `npm run test` 94/94 ✓ (38 unhandled errors) | Publisher 11/11 ✓ | mqtt2mail 0 Tests ✗

---

## 🔴 Kritisch (Funktion / Sicherheit / Deploy)

| # | Bereich | Problem | Ort |
|---|---------|---------|-----|
| K1 | Infra | **Mosquitto-Port-Bug:** `mosquitto.conf` lauscht nur auf **2883**, aber `.env.example`/`.env` setzen `MQTT_PORT=1883`. Der gebündelte Broker ist intern auf Port 1883 nicht erreichbar. TSD §6 (Z.2134) behauptet fälschlich „1883 matches the dev Mosquitto listener". | `src/mosquitto/config/mosquitto.conf` vs `src/.env.example:15` |
| K2 | Sicherheit | **MQTT-TLS-Verifikation permanent deaktiviert:** `check_hostname=False` + `verify_mode=CERT_NONE` werden bei `tls=True` IMMER gesetzt. `MQTT_TLS_INSECURE` ist dokumentiert wird aber **nie ausgelesen** → MITM-Risiko für **beide** Dienste (Backend + mqtt2mail Produktion). | `src/backend/mqtt.py:83-84`, `src/mqtt2mail/app/mqtt2mail.py:747-751` |
| K3 | Sicherheit | **Echte Produktions-Secrets im Workspace:** `src/.env_production` enthält reale Credentials (`API_TOKEN`, `MQTT_PASS`, `AI_API_KEY=sk-…`, `SMTP_PASSWORD`). Korrekt gitignored (nicht committet) aber im Klartext auf Disk. `deploy-prepare.sh:12` kopiert sie nach `deploy/.env`. | `src/.env_production` |
| K4 | Backend | **Rate-Limiter Memory-Leak:** Nach `bucket.append(now)` ist der Bucket nie leer → `if not self.requests[client_ip]:` auf Zeile 284 feuert nie. IP-Buckets werden nie geräumt → unbegrenztes Wachstum von `self.requests`. | `src/backend/main.py:281-285` |
| K5 | Backend | **Pump-Throttle verwirft 2. Pumpe:** Der Throttle-Key ist **Pool** statt `(pool, pump)`. Wechseln Haupt- und Solarpumpe gleichzeitig wird das zweite Event nie in `pump_events` persistiert (In-Memory-State aktualisiert sich korrekt). | `src/backend/main.py:202-204`, `_should_persist_pump_event` |

---

## 🟠 Wichtig (Doku-Drift / Stale Kopien / Test-Lücken)

| # | Bereich | Problem | Ort |
|---|---------|---------|-----|
| W1 | Doku | **README massiv veraltet (Pre-Phase-23/25):** dokumentiert `POST /api/chem` + `<pool-topic>/chem` (Z.18-19, 76), `LIVE_TOPIC_BLE/PUMP_TEMPLATE` (Z.61-62, in Phase 23 entfernt), View „chemistry" (Z.108), MQTT-Port „2883" (Z.56) widerspricht `.env.example` (1883). | `README.md` |
| W2 | Doku | **`.env.example` stale:** Kommentare Z.6-9 und 47-51 nennen `<base>/chem` und „chemistry messages" statt `/event` (Phase 25 Rename). | `src/.env.example` |
| W3 | Doku | **mqtt2mail-README dokumentiert entfernte Env-Vars:** `MQTT_TOPICS`, `MQTT_TOPIC_BASE`, `MQTT_ALERT_TOPICS`, `MQTT_AVAILABILITY_TOPICS` (die in Phase 23.4 entfernte Prioritätskette). | `src/mqtt2mail/README.md:81-100` |
| W4 | Doku | **Plan/Code-Mismatch:** Phase 23.5 verifiziert `python publisher.py --pool X --kind ble` — der Publisher hat **kein CLI** (kein argparse). Auch `POOL_BASE_TOPICS` als Env-Var (23.5.1) existiert nicht; Dict wird aus `POOL_LIST` abgeleitet (23.6.6 widerspricht 23.5.1). | `src/dev/mqtt-publisher/publisher.py:240`, `plan.md:798-805` |
| W5 | Tests | **mqtt2mail hat 0 Tests** — 823 Zeilen logikschwerer Code (Topic-Resolution, Scheduling, Mail-Building, Batterie-Umrechnung, Wildcard-Matching) ungetestet. Der triviale Publisher hat 11 Tests. | `src/mqtt2mail/` |
| W6 | Tests | **38 unhandled errors** in Vitest (uPlot-Async-Fehler in LiveView/TrendChart nach Test-Ende) — Tests nominell grün aber laut. | `tests/LiveView.spec.js`, `tests/TrendChart.spec.js` |
| W7 | Infra | **Deploy-Skript kopiert Mosquitto-Konfig nicht:** `deploy-prepare.sh:41-42` auskommentiert → `docker-compose.yml` im Deploy-Paket referenziert `./mosquitto/config` (leeres Mount) → Mosquitto startet mit Default-Config (1883 statt 2883, anonymous false). | `src/deploy-prepare.sh` |
| W8 | Infra | **`deploy/` ist eine veraltete Kopie:** enthält noch `APP_VERSION="1.0.0"`, `/chem`, `RESERVED_SUFFIXES=("manual","chem","pump")`. Wird durch `deploy-prepare.sh` regeneriert, ist gitignored. | `deploy/backend/main.py` |
| W9 | Infra | **`depends_on: mosquitto` auskommentiert** für Backend und mqtt2mail — Startup-Reihenfolge nicht enforced (Container starten parallel, verlassen sich auf reconnect). | `src/docker-compose.yml:23-24,49-50` |
| W10 | Doku | **TSD behauptet falsch:** „MQTT_PORT=1883 matches the dev Mosquitto listener" — der Dev-Broker lauscht auf **2883**. | TSD §6 (Z.2134) |

---

## 🟡 Frontend-Befunde

| # | Problem | Schwere | Ort |
|---|---------|---------|-----|
| F1 | **`PumpStatusCard` Sekunden-statt-Minuten-Bug:** `sinceMinutes = floor(now - runningSince)` liefert Sekunden (Unix-Timestamp-Differenz) wird aber als „läuft seit N min" ausgegeben. h/m-Split ab 60 deshalb falsch. | Funktion | `PumpStatusCard.vue:18-31` |
| F2 | **`package.json` Version `1.0.0`** statt `2.0` — SettingsPanel zeigt korrekt `2.0`, Backend `APP_VERSION=2.0`. | Konsistenz | `frontend/package.json:4` |
| F3 | **Nicht-germanisierte Strings:** `ImageCaptureModal.vue` (Z.39-58 Fehlertexte, Z.84 „Analyzing image…") + `EventForm.vue` 401-Toast (Z.178) und Button `SEND`/`Sende...` (Z.284). Phase 26 nur teilweise umgesetzt. | UI-Konsistenz | s.l. |
| F4 | **Inkonsistente Umlaute:** ASCII-Workarounds (`oeffnen`/`auswaehlen`/`groesser`) in `App.vue`/`EventForm.vue` vs. korrekte Umlaute (`prüfen`/`LÄUFT`/`läuft`) in `MeasurementForm.vue`/`PumpStatusCard.vue`. | UI-Konsistenz | s.l. |
| F5 | **`NAME_CONFIG` fehlt** in `validation.js` — Plan Z.98/143 + TSD Z.646 fordern `{minLength:1,maxLength:50,pattern:/^[a-zA-Z0-9 ]+$/}`. Name-Pattern wird im Frontend nie validiert (Backend prüft nur `POOL_NAMES`-Membership). | Funktion | `src/validation.js` |
| F6 | **`tests/useSettings.spec.js` testet Kopie statt Modul:** eigene `load/save` mit nicht-existentem `backendUrl` — importiert das echte Composable nicht. | Tests | `tests/useSettings.spec.js` |
| F7 | **Dead Code:** `StepperInput.vue` (nur im Test, durch `ValueSliderInput` ersetzt in Phase 7), `useApi().fetchPumpEvents` (exportiert/getestet aber nie in UI verwendet), `LiveView.persistentError` (computed nie im Template). | Cleanup | s.l. |
| F8 | **Fehlende Tests:** TSD §8.2 listet `tests/MeasurementForm.spec.js` — existiert nicht. | Tests | `tests/` |
| F9 | **Accessibility:** Icon-Buttons (+/−, Eye-Toggle) ohne `aria-label`; einige `<select>`/`<input datetime-local>` unter 44px Touch-Target-Minimum. | UX | s.l. |

---

## 🟡 Backend-Befunde

| # | Problem | Schwere | Ort |
|---|---------|---------|-----|
| B1 | **Dead Code / Unused Imports:** `from collections import defaultdict` (`main.py:8`), `PUMP_FIELDS = ("mainPump","solarPump")` (`:82` nie referenziert), `RESERVED_SUFFIXES` (`:115` nur Dokumentation), `_base_to_pool()` (`:144-146` nie aufgerufen), `FRONTEND_URL` doppelt gelesen (`:52`+`:59`), `AI_MAX_IMAGE_BYTES` doppelt (`main.py:62`+`ai.py:30`), `Iterable` in `db.py:15`. | Cleanup | s.l. |
| B2 | **`python-dotenv` in `requirements.txt`** aber nie importiert (Env kommt via `env_file` aus Compose). | Dependencies | `requirements.txt:4` |
| B3 | **`AI_IMAGE_RETENTION_DAYS` Default-Mismatch:** Code = `30` (`ai.py:29`), `.env.example:30` = `60`. | Konfig | s.l. |
| B4 | **`/api/status` unauthentifiziert** — gibt Version MQTT-Status Uptime AI-Config Request-Counts DB-State preis (Health-Check, aber Info-Disclosure). | Sicherheit | `main.py:610` |
| B5 | **429-Antworten ohne CORS-Header:** Rate-Limit-Middleware ist äußere Middleware (vor CORS) → Browser sieht generischen Fehler statt JSON-429. | UX | `main.py:472` |
| B6 | **Test-Smells:** `test_api_live.py:19` patcht nicht-existentes `_topic_to_pool_map` (wirkungslos, real: `_base_to_pool_map`); `test_api.py:377,398` übergeben nicht-existentes `time=`-Feld an `ImageAnalysisResult` (Pydantic ignoriert still). | Tests | s.l. |
| B7 | **Aggregator:** letztes Teilfenster wird bei Shutdown nie geflusht (Datenverlust < window-Minuten); Ring-Buffer (5) kann bei >5 Samples/30s Samples verlieren. | Funktion | `aggregator.py` |

---

## 🟡 mqtt2mail-Befunde

| # | Problem | Schwere | Ort |
|---|---------|---------|-----|
| M1 | **Permanenter Debug-`print`** aller Topics+Payloads nach stdout, unabhängig von `LOG_LEVEL` — leakt alle Sensordaten in Container-Logs. | Security/Production | `mqtt2mail.py:770` |
| M2 | **`<b>`-HTML-Tags im text/plain Mailteil** → Klartext-Clients zeigen rohe Tags. | Funktion | `mqtt2mail.py:459,466,617` |
| M3 | **Dead Code:** `parse_topic_csv()` (nie aufgerufen), alle `availability_*`-Zweige (immer leer → unerreichbar), `_drive_loop` im Test (nie aufgerufen intern kaputt da `stop_flag` nicht existiert). | Cleanup | s.l. |
| M4 | **Event-Payloads inflationieren `message_count`:** landen in `add_data()` (weil `<base>/+` matcht) und zählen obwohl ohne Metrik-Keys ignoriert → „Empfangene Messungen" zu hoch. | Funktion | `mqtt2mail.py:341,502` |
| M5 | **Anonymes MQTT erlaubt:** Credentials nur gesetzt wenn Username nicht-leer. `.env.example` hat leere Defaults. | Security | `:744-745` |

---

## 🟢 Positiv (was gut läuft)

- **Token-Vergleich** constant-time via `secrets.compare_digest`
- **MQTT-Wildcard-Matching** (`+`/`#`) korrekt implementiert und getestet
- **SQLite** WAL + `threading.Lock` sauber; Schema-Migration-idempotent
- **SMTP-STARTTLS** mit verifiziertem SSL-Context (im Gegensatz zu MQTT)
- **CSP / Security-Header** im Caddy-Production-Block gesetzt
- **Container:** non-root User (bis auf Publisher), Alpine-Base, gepinnte Tags (Phase 24)
- **`.env`-Dateien** korrekt von git ignored (nur `.env.example` getrackt)
- **Backend-Tests** umfassend (185) — insb. Handler-Dispatch, Wildcard-Matching, Validatoren, Aggregator, Live-State

---

## Überblick Testabdeckung

| Suite | Tests | Status |
|-------|-------|--------|
| Backend (`src/backend`) | 185 | ✅ Alle grün (1 Deprecation-Warning) |
| Frontend (`src/frontend`) | 94 | ✅ Alle grün (⚠️ 38 unhandled uPlot-Errors) |
| Publisher (`src/dev/mqtt-publisher`) | 11 | ✅ Alle grün |
| mqtt2mail (`src/mqtt2mail`) | **0** | ❌ Keine Tests vorhanden |
| **Gesamt** | **290** | |

---

## Commit-Empfehlung (für das Skill)

```bash
git add .agents/skills/pool-monitoring/
git add docs/analyse/projekt-analyse-2026-06-09.md
git commit -m "docs: add project analysis and pool-monitoring skill [OpenCode / deepseek-v4-flash-free]"
```
