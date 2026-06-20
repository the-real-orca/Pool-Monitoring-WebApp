# Pool Dashboard – Projektskizze

## Übersicht

**Pool Dashboard** ist ein paralleles Projekt zur Pool-Monitoring App – ein eigenständiger Stack (eigenes FastAPI-Backend + Vue-3-Frontend) im selben Docker-Compose-Setup, als **Sub-Path** auf dem internen Server.

**Zweck:** Steuerung und Überwachung der Pooltechnik (Filterpumpe, Solarpumpe) sowie Anzeige von Wasserparametern, Alarmen, Ereignissen und historischen Daten.

**Zielgerät:** 14"-Tablet (1024×800) im Technikraum – internes Netzwerk, kein Login.

---

## Datenquellen

| Daten | Quelle | Zugriff |
|-------|--------|---------|
| Wasserwerte (Temp, pH, Cl) | BLE-YC01 → Externer MQTT | Dashboard-Backend subscribed |
| Historische Messwerte (7d) | Pool-Monitoring SQLite | Read-only Volume-Mount |
| Events (Chlor, Nachfüllen…) | Pool-Monitoring → MQTT → Service → TimescaleDB | Read-only via psycopg2 |
| Filterpumpen-Status | Tasmota → Interner MQTT | Dashboard-Backend subscribed |
| Solarpumpen-Status | Tasmota Energy → Interner MQTT | Aus Power Consumption abgeleitet |
| Pumpen-Zeitplan | Tasmota Timers | Read/Write per MQTT (cmnd) |
| Pumpen-Strom | Tasmota Energy → Interner MQTT | Schwellwert-Überwachung |

---

## Architektur-Entscheidungen

| Entscheidung | Wert |
|-------------|------|
| Beziehung zu Pool-Monitoring | Eigenständiger separater Stack |
| Backend | Python FastAPI (eigener Service) |
| Frontend | Vue 3 + Tailwind CSS + uPlot |
| Charting | uPlot (wie Pool-Monitoring) |
| DB Historie | Pool-Monitoring SQLite (read-only) |
| DB Events | TimescaleDB (read-only, bestehender Container) |
| MQTT Sensor-Daten | Externer Broker (gemeinsam mit Pool-Monitoring) |
| MQTT Pumpen-Steuerung | Interner Broker (bestehender Container, Tasmota) |
| Alarm-Logik | Dashboard-Backend (eigener Service) |
| Deployment | Sub-Path auf internem Server |
| Event-Quelle | Aus TimescaleDB lesen (Update beim Seitenöffnen) |
| Layout | Noch offen (TODO – aus dashboard-examples/) |

---

## Pumpen-State-Machine

```
ZEITPLAN  ──►  DAUERLAUF  ──►  ZEITPLAN (nach Timer)
ZEITPLAN  ──►  AUS
AUS       ──►  ZEITPLAN / DAUERLAUF
DAUERLAUF ──►  AUS
```

- **ZEITPLAN:** Tasmota-Timer aktiv
- **DAUERLAUF:** Pumpe für N Stunden eingeschaltet (Timer ändert Tasmota-Konfiguration NICHT)
- **AUS:** Pumpe aus (Override)

---

## Seiten

| Seite | Inhalt |
|-------|--------|
| **Dashboard** | Messwerte (Temp/pH/Cl), Pumpen-Status, 7d-Chart, aktive Alarme, Zeitplan-Übersicht, Aktionen |
| **Zeitplan** | Ein-Tag-Ansicht, 15-Min-Slots, Edit-Mode-Toggle, Speichern per MQTT an Tasmota |
| **Alarme & Ereignisse** | Aktuelle/vergangene Alarme, Event-Liste aus TimescaleDB |
| **Konfiguration** | MQTT-Server, Chemie-Schwellwerte, Pumpen-Strom, Dauerlauf-Dauer |

---

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| GET | `/api/live` | Aktuelle Sensorwerte + Pumpenstatus |
| GET | `/api/history` | Historische Daten (Metric, Tage) |
| GET | `/api/pump/status` | Pumpen-Modi und States |
| POST | `/api/pump/override` | Dauerlauf setzen (mode, durationMinutes) |
| GET | `/api/schedule` | Zeitplan von Tasmota lesen |
| POST | `/api/schedule` | Zeitplan an Tasmota schreiben |
| GET | `/api/alarms` | Aktive + vergangene Alarme |
| POST | `/api/alarms/:id/ack` | Alarm quittieren |
| GET | `/api/events` | Ereignis-Liste aus TimescaleDB |
| GET/POST | `/api/config` | Konfiguration lesen/schreiben |

---

## Technologie-Stack

| Komponente | Technologie |
|-----------|-------------|
| Frontend | Vue 3 (Composition API), JavaScript, Tailwind CSS, Vite |
| Charts | uPlot (Canvas, Touch-Zoom/Pan) |
| Backend | Python FastAPI, paho-mqtt, sqlite3, psycopg2 |
| DB History | Pool-Monitoring SQLite (read-only) |
| DB Events | TimescaleDB (read-only) |
| MQTT Ext | Externer Mosquitto (Sensor + Events) |
| MQTT Int | Interner Mosquitto (Tasmota) |
| Deployment | Docker Compose, Caddy Sub-Path, Nginx |

---

## Dateistruktur (geplant)

```
dashboard/
├── docs/
│   ├── Pool-Dashboard - Projekt Idee.md
│   ├── Pool-Dashboard - Skizze.md
│   ├── Pool-Dashboard - Functional Specification (FSD).md
│   ├── roadmap.md
│   └── dashboard-examples/
├── backend/
│   ├── main.py
│   ├── mqtt_ext.py
│   ├── mqtt_int.py
│   ├── live_state.py
│   ├── pump_state.py
│   ├── alarms.py
│   ├── db_history.py
│   ├── db_events.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── components/
│   │   │   ├── DashboardView.vue
│   │   │   ├── ScheduleView.vue
│   │   │   ├── AlarmEventView.vue
│   │   │   └── ConfigPanel.vue
│   │   └── composables/
│   │       ├── useApi.js
│   │       ├── useLiveData.js
│   │       ├── useAlarms.js
│   │       └── useSchedule.js
│   ├── public/
│   └── Dockerfile
```
