# Pool MQTT Mailer

Kleiner MQTT-Report-Gateway fuer Pool-Messwerte und Alarme.

Aktueller Testmodus: Der Report wird alle `REPORT_INTERVAL_SECONDS` nach stdout geschrieben. SMTP/Gmail-Versand ist im Code bewusst deaktiviert.

## Architektur

```text
MQTT Broker -> Python Docker Container -> RAM Aggregation -> stdout Report alle 15 Minuten
```

Im Pool-Monitoring-Projekt laeuft der Container als Service `pool-mqtt-mailer` in
`src/docker-compose.yml` und nutzt dieselbe `src/.env` wie das Backend.

Das Skript speichert nur die fuer das naechste Report-Fenster relevanten Werte im RAM:

- letzter Messwert pro Kennzahl
- min/max seit letztem Report
- Mittelwert der letzten 5 Messungen pro Kennzahl
- Alarm-/Recovery-Meldungen seit letztem Report
- aktuelle Availability

Nach einem Container-Neustart beginnt ein neues Sammelfenster. Nicht ausgegebene Werte gehen dabei bewusst verloren.

## Wichtige Aenderung: Schwellwerte nur aus Alert-Messages

Es gibt keine festen Schwellwerte mehr im Programm und keine Grenzwert-Konfiguration in `.env`.

Schwellwerte werden nur dann beruecksichtigt, wenn sie in einer Alert-Message enthalten sind:

```json
{
  "alert": true,
  "type": "cl",
  "value": 0.1,
  "min": 0.5,
  "max": 1.4,
  "text": "Alert: cl too low"
}
```

Verhalten:

- Alert- und Recovery-Meldungen erscheinen im Abschnitt `Warnung`.
- Der zuletzt empfangene Alert pro Messgroesse liefert den angezeigten `Soll`-Bereich in der Uebersicht.
- Werte werden in der Uebersicht nur fett markiert, wenn fuer diese Messgroesse im aktuellen Report-Fenster zuletzt ein aktiver Alert (`alert: true`) empfangen wurde.
- Wenn keine Alert-Message fuer eine Messgroesse kommt, wird fuer diese Messgroesse kein Sollbereich ausgewertet und kein Wert wegen Grenzwerten markiert.

## Dateien

```text
pool-mqtt-mailer/
├── Dockerfile
├── requirements.txt
├── .env.example
└── app/
    └── mqtt2mail.py
```

## Integration im Hauptprojekt

```bash
cp src/.env.example src/.env
nano src/.env
cd src && docker compose up -d --build pool-mqtt-mailer
```

Logs und Reports anzeigen:

```bash
cd src && docker compose logs -f pool-mqtt-mailer
```

Stoppen:

```bash
cd src && docker compose stop pool-mqtt-mailer
```

## MQTT Topics

Topic-Auswahl (Prioritaet):

1. `MQTT_TOPICS`, `MQTT_ALERT_TOPICS`, `MQTT_AVAILABILITY_TOPICS`
2. Topics aus `POOL_LIST` (automatisch aus Pool-Monitoring)
3. Fallback: `MQTT_TOPIC_BASE` (+ `/alert`, `/availability`)

Beispiel mit expliziten Topics:

```text
home/H32/pool/manual
home/H32/whirlpool/manual
```

Konfiguration ueber `.env`:

```env
MQTT_TOPICS=home/H32/pool/manual,home/H32/whirlpool/manual
```

## Fehlertoleranz

Das Skript ist tolerant gegenueber fehlenden JSON-Feldern:

- Fehlende Messwerte werden ignoriert.
- Nicht numerische Werte werden ignoriert.
- Ungueltiges JSON wird gezaehlt und nicht verarbeitet.
- Fehlende `min`/`max` Felder in Alert-Messages werden als `n/a` dargestellt.

## Batteriewerte

Batteriewerte werden im Beispiel als mV geliefert. Deshalb gilt standardmaessig:

```env
BAT_VALUE_UNIT=mv
BAT_DISPLAY_UNIT=V
```

`2450` wird dadurch als `2,45 V` dargestellt. Das gilt sowohl fuer normale Messwerte als auch fuer Alert-Messages vom Typ `bat`.

## Test mit mosquitto_pub

```bash
mosquitto_pub -h mqtt.example.com -t /esp32/sensor/ble-yc01 -m '{"name":"PoolSensor","pH":7.32,"cl":0.1,"temp":26.8,"bat":2980}'

mosquitto_pub -h mqtt.example.com -t /esp32/sensor/ble-yc01/alert -m '{"alert":true,"type":"cl","value":0.1,"min":0.5,"max":1.4,"text":"Alert: cl too low"}'

mosquitto_pub -h mqtt.example.com -t /esp32/sensor/ble-yc01/alert -m '{"alert":false,"type":"cl","value":0.8,"min":0.5,"max":1.4,"text":"Recovery: cl back in range"}'
```

Fuer schnelle Tests kann das Intervall temporaer reduziert werden:

```env
REPORT_INTERVAL_SECONDS=60
```
