# PWA Offline Test Plan

## Ziel
Testen, ob die Pool-Monitoring PWA im Offline-Modus funktioniert.

## Voraussetzungen

- Frontend ist gebaut (`npm run build`)
- Caddy/Server läuft
- PWA ist im Browser installiert

## Test-Schritte

### Schritt 1: Service Worker Registrierung prüfen

1. Browser DevTools öffnen (F12)
2. **Application** Tab → **Service Workers**
3. Status sollte "Activated and running" zeigen
4. Prüfen: `sw.js` ist registriert

**Erwartetes Ergebnis:** Service Worker ist aktiv

---

### Schritt 2: Online-Modus - Messung senden

1. PWA im Browser öffnen (online)
2. Messung ausfüllen:
   - Temperatur: 25.0
   - pH: 7.2
   - Chlor: 1.5
3. "Senden" Button klicken
4. Toast-Erfolgsmeldung prüfen

**Erwartetes Ergebnis:** Erfolgreich gesendet

---

### Schritt 3: Offline-Modus - Messung senden

1. **DevTools → Network** Tab
2. "Offline" aktivieren (Dropdown: "No throttling" → "Offline")
3. Seite neu laden (F5)
4. Messung ausfüllen:
   - Temperatur: 26.0
   - pH: 7.3
   - Chlor: 1.6
5. "Senden" klicken

**Erwartetes Ergebnis A (funktioniert):**
- Kein Netzwerk-Fehler
- Daten werden gecached

**Erwartetes Ergebnis B (funktioniert nicht):**
- "Network error" Toast erscheint
- Seite funktioniert nicht im Offline-Modus

---

### Schritt 4: Cache prüfen (nach Schritt 3)

1. **DevTools → Application → Cache Storage**
2. Prüfen ob Messungen gecached sind

**Erwartetes Ergebnis:** Cached Daten vorhanden (wenn implementiert)

---

### Schritt 5: Zurück Online

1. "Offline" in Network-Tab deaktivieren
2. Prüfen ob queued Daten automatisch gesendet werden (wenn implementiert)

---

## Ergebnis-Dokumentation

| Test | Schritt | Erwartet | Ergebnis | Notes |
|------|---------|----------|----------|-------|
| 1 | Service Worker aktiv | Ja/Nein | | |
| 2 | Online-Senden | Erfolg/Fehler | | |
| 3 | Offline-Senden | Erfolg/Fehler | | |
| 4 | Cache vorhanden | Ja/Nein | | |
| 5 | Auto-Sync | Ja/Nein | | |

---

## Fazit

- **Wenn alle Tests bestehen:** CSP ist OK, PWA offline funktioniert
- **Wenn Test 3 fehlschlägt:** CSP muss erweitert werden (`worker-src 'self'`)
- **Wenn Test 4 fehlschlägt:** Background Sync muss implementiert werden