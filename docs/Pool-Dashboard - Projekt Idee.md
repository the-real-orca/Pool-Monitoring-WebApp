# Pool Dashboard

Web App auf Tablet
Internes Netzwerk, kein Login notwendig.

## GUI

helles, modernes, klar strukturierte Web Page

### Dashboard (Hauptseite)
 - aktuelle Messwerte (Wassertemp, pH, Chlor)
 - historische Daten (1 woche) als Diagramm
 - Filterpumpen und Solarpumpen Status
 - Zeitplan für Filterpumpe
 - Aktionen 
    - Filterpumpe aus, ein (für nächsten 2 h), automatik (Zeitplan)
    - Zeitplan -> eigene Einstellungsseite
    - Konfigurationsseite

### Zeitplan
 - Tagesübersicht mit Slots (15min) wann Filterpumpe an / aus ist

## API

die gesamte Kommunikation läuft via MQTT

### Messwerte
Messwerte -> data.sample.json (siehe Pool-Monitoring Projekt)

### Historische Daten
 - Messwerte
 - wann Pumpen tatsächlich gelaufen sind

### Filterpumpe
 - Pumpen -> gesteuert via Tasmota
 - Zeitplan über Tasmota verwalten
 - Pumpe kann auf manuellen dauerlauf gestellt werden. Nach 2 Std. (konfigurerbar) wechselt sie autom. zum Zeitplan zurück.
 - Pumpenzeitplan kann manuell deaktiviert werden

### Solarpumpe
 - Solarpumpe ist temperaturgesteuert (autom. Regler)
 - Tasmota -> Power zeigt Status (an / aus)


