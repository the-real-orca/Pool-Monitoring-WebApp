# Benchmark-Vergleich: Top 5 Modelle (alle 33 Bilder)

**Datum:** 2026-05-27  
**Einstellungen:** `AI_PH_TOLERANCE=1.0`, `AI_CL_TOLERANCE=1.0`, `AI_CL_TOLERANCE_STOPS=1.0`

## Rangliste (33 Bilder)

| Rang | Modell | Ø Total | Bestanden | Gesamtkosten | ∅ Kosten/Bild |
|-----:|--------|--------:|----------:|-------------:|--------------:|
| 1 | Gemini 3.5 Flash | **60.2%** | **21/33** | $0.7311 | $0.0222 |
| 2 | Gemini 3 Flash Preview | **56.6%** | 20/33 | **$0.0282** | **$0.0009** |
| 3 | Gemini 2.5 Pro | **53.5%** | **21/33** | $0.4636 | $0.0140 |
| 4 | Gemini 3.1 Pro Preview | **52.2%** | 18/33 | $0.8735 | $0.0265 |
| 5 | Claude Opus 4.7 | **39.2%** | 14/33 | $0.5401 | $0.0164 |

---

## Analyse

### Wichtigste Erkenntnisse

**Gemini 3.5 Flash** ist der Gesamtsieger mit 60.2% ∅ und den meisten bestandenen Bildern (21/33). Die pH-Erkennung ist sehr solide, Cl zeigt gelegentlich Ausreißer bei hohen Werten.

**Gemini 3 Flash Preview** bietet das **beste Preis-Leistungs-Verhältnis**: 56.6% bei nur **$0.0009/Bild** – das ist Faktor 25× günstiger als Gemini 3.5 Flash und Faktor 30× günstiger als Claude Opus 4.7. Für 80% der Performance bei <5% der Kosten die klare Empfehlung.

**Gemini 2.5 Pro** und **Gemini 3.1 Pro Preview** liegen im Mittelfeld (52–53%), aber Gemini 3.1 Pro Preview ist mit $0.87 fast doppelt so teuer wie Gemini 2.5 Pro.

**Claude Opus 4.7** fällt mit 39.2% deutlich ab – das Modell halluciniert häufiger Werte bei Bildern ohne Referenzskala (gibt pH=7.2 statt -1 zurück) und hat große Probleme mit hohen Cl-Werten (7.0–10.0 ppm).

### Schwächen aller Modelle

- **Hohe Cl-Werte (7.0–10.0 ppm):** Kein Modell erkennt Cl > 5.0 ppm zuverlässig. Die Farbskala ist in diesem Bereich sehr ähnlich (dunkel orange).
- **Fehlende Referenzskala:** Nur Gemini 3 Flash Preview und Gemini 3.1 Pro Preview geben konsequent -1 zurück. Claude Opus 4.7 und Gemini 2.5 Pro hallucinieren stattdessen Werte.
- **Doppelte Teststreifen:** Bilder mit zwei Testsystemen verwirren alle Modelle.

### Kostenvergleich

| Modell | Gesamtkosten (33 Bilder) | Kosten für 1.000 Analysen |
|--------|-------------------------:|--------------------------:|
| Gemini 3 Flash Preview | $0.028 | **$0.85** |
| Gemini 2.5 Pro | $0.464 | $14.05 |
| Claude Opus 4.7 | $0.540 | $16.37 |
| Gemini 3.5 Flash | $0.731 | $22.15 |
| Gemini 3.1 Pro Preview | $0.874 | $26.47 |

---

**Fazit:** Für Produktion ist **Gemini 3.5 Flash** die erste Wahl (beste Genauigkeit). Für Entwicklung/Testing oder bei Budget-Einschränkungen ist **Gemini 3 Flash Preview** mit $0.85/1.000 Analysen unschlagbar.
