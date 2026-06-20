
In @"Pool-Dashboard - Projekt Idee.md" befindet sich eine Stichwortartige Projektidee. Das Pool Dashboard soll ist ein Parallellprojekt zur Pool-Monitoring App.
Analysiere die Projektidee und kläre interaktiv noch offene bzw. nicht detailiert genug beschriebene Punkte ab, umd daraus eine klare und vollständige Projektskizze zu erstellen.


# Pool Dashboard


Die App dient dazu die Pooltechnik (Filterpumpe, Solarpumpe) zu steuern und zu überwachen. Auferdem sollen die aktuellen Wasserparameter (Temp, pH, Cl) sowie Historische Daten (Wochen Diagramm) und Trend angezeigt Werden. Die MEsswerte kommen von einem BLE-YC01 Sensor via MQTT.
Außerdem sollen Alarmmeldungen (z.B. pH zu hoch, etc.), Trendalarme (cl sinkt, bald nachfüllen) sowie eine Eventliste (z.B. Wasser nachgefüllt am 30.6.2026) angezeigt werden. Die Messwerte und Events sind entweder live über MQTT oder eine DB (im intranet) verfügbar.
Web App auf kleinem Tablet (14", 1024x800). Tablet im Technikraum neben Pool.
Das Dashboard soll parallel zur Pool Monitoring App laufen.
Internes Netzwerk, kein Login notwendig.

## GUI

helles, modernes, klar strukturierte Web Page / Dashboard
gute touch Bedienbarkeit (klare und große Buttons)
Bspl Layout findet sich in dashboard-examples/dashboard-layout.png 


### Dashboard (Hauptseite)
 - aktuelle Messwerte (Wassertemp, pH, Chlor)
 - historische Daten (1 Woche) als Diagramm (in Messwert Box)
 - Filterpumpen und Solarpumpen Status (on / off / unknown)
 - Zeitplan für Filterpumpe
 - aktuelle Alarme (Chemie außerhalb der Grenzwerte, Pumpe braucht mehr Strom als normal, etc.)
 - Aktionen
    - Filterpumpe aus, ein (befristetes einschalten, für nächsten 2 Std), automatik (Zeitplan)
    - Zeitplan -> eigene Zeitplan Seite
	- Alarm / Ereignissübersicht
    - Konfigurationsseite

### Zeitplan
 - Tagesübersicht mit Slots (15min) wann Filterpumpe an / aus ist
 - Bearbeitungsmodus extra aktivieren, um versehendliche Änderungen zu vermeiden


### Alarm / Ereignissübersicht
 - aktuelle und vergangene Alarme
 - liste mit Ereignissen (Chemie nachgefüllt, etc.)
 - ...

### Konfigurationsseite
 - MQTT Server & Topics
 - Schwellwerte für Chemie
 - Schwellwert für Pumpe (Strom)
 - ...

## API

### Messwerte

 - externer MQTT Server
 - Sensor schickt automatische Messwerte via MQTT
 - Pool App schickt manuelle Messwerte via MQTT
 - Messwerte -> data.sample.json (siehe Pool-Monitoring Projekt)

### Historische Daten
 
 - Messwerte
 - wann Pumpen tatsächlich gelaufen sind
 - Datenspeicher ???? interne Postgress / TimeDB?

### Filterpumpe
 - daten und commands via internen MQTT Server
 - Pumpen -> gesteuert via Tasmota (siehe Tasmota Dokumentation)
 - Zeitplan über Tasmota konfigurieren, Dashboard ist nur Visualisierung kein Controller
 - Filterpumpe kann auf (befristeten) manuellen Dauerlauf gestellt werden. Nach 2 Std. (konfigurerbar) wechselt sie autom. zum Zeitplan zurück.
 - Pumpenzeitplan kann manuell deaktiviert werden -> Pumpe aus / manueller Dauerlauf

### Solarpumpe
 - Solarpumpe ist temperaturgesteuert (autom. Regler, nicht Teil des Projekts)
 - Tasmota -> Status aus Power Konsumption ableiten (on / off)



