# Pool Dashboard – Implementierungsplan

---

## Phase 1: Infrastruktur & Grundgerüst

- [ ] Verzeichnisstruktur anlegen (`dashboard/backend/`, `dashboard/frontend/`)
- [ ] `dashboard/backend/Dockerfile` erstellen (Python FastAPI)
- [ ] `dashboard/frontend/Dockerfile` erstellen (Node/Vite-Build + Nginx)
- [ ] `dashboard/frontend/nginx.conf` für SPA-Routing erstellen
- [ ] Services in `docker-compose.yml` eintragen (`dashboard-frontend`, `dashboard-backend`)
- [ ] Caddy-Routing für Sub-Path `/dashboard/*` erweitern
- [ ] `mqtt2db` Bridge-Service in `docker-compose.yml` (subscribes Ext MQTT, schreibt in TimescaleDB)
- [ ] Basis-Test: Beide Container starten, Caddy antwortet auf `/dashboard/`

---

## Phase 2: Backend-Grundgerüst

- [ ] `main.py` – FastAPI-App, Pydantic-Models, Config (os.getenv), JSON-Config-Persistenz
- [ ] `mqtt_ext.py` – MQTT-Client für externen Broker (Live-Sensor-Daten)
- [ ] `mqtt_int.py` – MQTT-Client für internen Broker (Tasmota)
- [ ] `live_state.py` – In-Memory Ringbuffer (temp/pH/Cl, 5 Samples)
- [ ] `db_timescale.py` – TimescaleDB-Reader (live, history, events)
- [ ] Endpunkte: `GET /api/live` (RAM via MQTT), `GET /api/history` (TimescaleDB)
- [ ] Tests: MQTT-Connection (ext + int), Ringbuffer, TimescaleDB-Read

---

## Phase 3: Frontend-Grundgerüst

- [ ] `App.vue` – View-Toggle (dashboard|schedule|alarms|config), Navigation
- [ ] Tailwind CSS Setup + Theme-Farben (wie Pool-Monitoring)
- [ ] `useApi.js` – Fetch-Wrapper mit API-Base-Path
- [ ] `useLiveData.js` – 10s-Polling für `/api/live`
- [ ] `DashboardView.vue` – Grundstruktur (Platzhalter für Karten)
- [ ] Vite + PWA-Setup (ohne Service-Worker, reine SPA)
- [ ] Tests: View-Switching, API-Wrapper, Polling

---

## Phase 4: Dashboard-Hauptseite – Live-Werte

- [ ] Sensor-Card-Komponente (Temp groß, pH/Cl mit Farbe)
- [ ] PumpStatusCard – Filterpumpe + Solarpumpe (Icon, Status, Laufzeit)
- [ ] Action-Buttons – AUTO / EIN / AUS / DAUERLAUF (vorerst ohne Backend-Anbindung)
- [ ] Stale-Badge bei veralteten Daten
- [ ] Loading / Empty / Error-States
- [ ] Tests: SensorCard, PumpStatusCard, DashboardView-Rendering

---

## Phase 5: Trend-Chart

- [ ] uPlot integrieren (npm-Paket)
- [ ] `TrendChart.vue` – 3 Panels (Temp/pH/Cl), gemeinsame X-Achse
- [ ] Touch-Interaktion: Pan (1-Finger), Zoom (Pinch), Reset (Double-Tap)
- [ ] Datenquelle: `GET /api/history` (TimescaleDB via mqtt2db-Bridge)
- [ ] Leerzustand: "Noch keine Daten"
- [ ] Cross-Chart-Sync (Zoom/Pan über alle 3 Panels)
- [ ] Tests: Chart-Instanzen, Touch-Gesten, Datenbindung

---

## Phase 6: Pumpen-Steuerung (Backend)

- [ ] `pump_state.py` – State Machine (ZEITPLAN / DAUERLAUF / AUS)
- [ ] Tasmota MQTT-Commands: POWER ON/OFF, Timer enable/disable
- [ ] `POST /api/pump/override` – Mode setzen (auto|manual|off)
- [ ] `GET /api/pump/status` – Aktuellen State abfragen
- [ ] Auto-Revert: DAUERLAUF → ZEITPLAN nach N Minuten
- [ ] Solarpumpen-Status aus Tasmota Power Consumption ableiten
- [ ] Tests: State-Machine-Transitions, MQTT-Command-Publish, Timer-Revert

---

## Phase 7: Pumpen-Aktionen (Frontend)

- [ ] Action-Buttons mit Backend-Anbindung (`POST /api/pump/override`)
- [ ] Dauerlauf-Dialog: Dauer eingeben (Slider/Stepper)
- [ ] Bestätigungs-Toast bei Erfolg, Error-Handling bei Fehler
- [ ] Aktualisierung PumpStatusCard nach Action
- [ ] Tests: Button-Klicks, API-Integration, Error-States

---

## Phase 8: Zeitplan-Seite

- [ ] `ScheduleView.vue` – 24h-Raster mit 15-Min-Slots (96 Slots)
- [ ] Tasmota-Timer lesen (`GET /api/schedule`) → Slots rendern
- [ ] Edit-Mode-Toggle (Bearbeitung nur nach Aktivierung)
- [ ] Slot-Toggle: Klick schaltet ON/OFF um
- [ ] Speichern (`POST /api/schedule`) – Slots → Tasmota Timer-Kommandos
- [ ] Cancel → Revert zu letztem gespeichertem Stand
- [ ] Mapping: Max 16 Timer (Tasmota-Limit), benachbarte Slots zusammenfassen (max. 8 aktive Zeit-Slots)
- [ ] Tests: Slot-Rendering, Edit-Mode, Timer-Mapping, Speichern/Laden

---

## Phase 9: Alarme (Backend)

- [ ] `alarms.py` – Alarm-Evaluierung bei jedem neuen MQTT-Sample (separate Diagramme für Range- und Power-Alarme)
- [ ] Range-Alarme: pH/Cl gegen Thresholds prüfen (ideal/acceptable/critical)
- [ ] Trend-Alarm: Cl-Verlauf über 24h (negativer Trend → "Chlor sinkt")
- [ ] Power-Alarm: Tasmota-Strom > konfigurierter Threshold (separater MQTT-Callback)
- [ ] Duplikat-Unterdrückung (gleicher Alarm-Typ max. alle 60 Min.)
- [ ] `GET /api/alarms` – Aktive + vergangene Alarme
- [ ] `POST /api/alarms/:id/ack` – Alarm quittieren
- [ ] Tests: Threshold-Logik, Trend-Erkennung, Duplikat-Suppression

---

## Phase 10: Alarm/Ereignis-Seite (Frontend)

- [ ] `AlarmEventView.vue` – Zwei Tabs: Alarme | Ereignisse
- [ ] Alarm-Liste: aktiv (hervorgehoben) / vergangen (abgedimmt)
- [ ] Alarm-Acknowledge-Button
- [ ] Ereignis-Liste aus `GET /api/events` (TimescaleDB)
- [ ] Reverse-chronologische Sortierung
- [ ] Tests: Tab-Switching, Alarm-Darstellung, Event-Liste

---

## Phase 11: Konfigurationsseite

- [ ] `ConfigPanel.vue` – Formular für alle Konfigurations-Werte
- [ ] `GET /api/config` – Aktuelle Config laden
- [ ] `POST /api/config` – Config speichern (Backend persistiert als JSON)
- [ ] Felder: MQTT-Hosts/Ports, Tasmota-Device-Topic, Thresholds, Dauerlauf-Dauer
- [ ] Validierung (leere Felder, Zahlenbereiche)
- [ ] Abbrechen → Revert, Speichern → Toast
- [ ] Tests: Form-Logik, API-Integration, Persistenz

---

## Phase 12: Layout & Touch-Optimierung

- [ ] Konkretes Layout aus dashboard-examples/ auswählen und umsetzen
- [ ] Touch-Optimierung: 44×44 px Mindestgrößen, ausreichend Abstände
- [ ] Kiosk-Modus-Optimierung: Vollbild, kein Scrollen nötig
- [ ] Responsive Anpassungen für 1024×800
- [ ] UI-Text: Finaler deutscher Text (Labels, Fehlermeldungen, Tooltips)

---

## Phase 13: Integration & Systemtest

- [ ] End-to-End-Test: Live-Daten → Dashboard-Anzeige
- [ ] End-to-End-Test: Pumpen-Override → Tasmota → Rückmeldung
- [ ] End-to-End-Test: Zeitplan schreiben → Tasmota → neu laden → bestätigen
- [ ] Fehlerszenarien: MQTT-Ausfall, DB nicht erreichbar, Tasmota offline
- [ ] Docker-Compose-Hochlauf-Test: alle Container starten, Caddy routet korrekt

---

## Phase 14: Deployment & Dokumentation

- [ ] `deploy-prepare.sh` für Dashboard aktualisieren (oder separates Skript)
- [ ] `.env.example` um Dashboard-Variablen erweitern
- [ ] README für Dashboard-Projekt schreiben
- [ ] CHANGELOG / Versioning (beginnt mit v1.0.0)
- [ ] Go-Live: Dashboard auf internem Server deployen, Tablet einrichten

---

## Legende

- [ ] = noch offen
- [x] = erledigt
