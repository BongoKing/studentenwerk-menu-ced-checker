# CED Mensa-Checker

Verträglichkeitsprüfung der Speisepläne des [Studierendenwerks Oberfranken](https://sls.swo.bayern) für Menschen mit **chronisch-entzündlichen Darmerkrankungen (CED)**.

Das Tool ruft täglich die Speisepläne der Uni Bayreuth ab (Hauptmensa, Frischraum, Salatbar), bewertet jedes Gericht auf Basis von Allergenen, Zusatzstoffen und Zutaten und erstellt eine farbcodierte Rangliste mit Benotung (A–F).

## Features

- **Zwei Krankheitsmodi:** Unterscheidung zwischen Morbus Crohn und Colitis ulcerosa
- **Automatische Bewertung:** Jedes Gericht erhält eine Note (A–F) basierend auf Allergenen, Zusatzstoffen und erkannten Zutaten
- **Anpassbare Konfiguration:** Zwei Excel-Dateien steuern die Bewertung — individuell editierbar (z.B. persönliche Unverträglichkeiten ergänzen)
- **Farbige Konsolenausgabe:** Rangliste mit Warnungen (rot) und empfohlenen Aspekten (grün)
- **Zeitraum-Reports:** Auswertung über mehrere Tage/Wochen als xlsx mit Detailübersicht, Tagesübersicht und Statistik
- **Flexibel erweiterbar:** Mensen, URLs und Kategorien über `settings.json` anpassbar

## Notensystem

| Note | Score | Bedeutung |
|------|-------|-----------|
| **A** | 9–10 | Sehr gut verträglich |
| **B** | 7–8 | Gut verträglich |
| **C** | 5–6 | Bedingt verträglich |
| **D** | 3–4 | Schlecht verträglich |
| **E** | 1–2 | Sehr schlecht verträglich |
| **F** | 0 | Ausgeschlossen |

## Installation

```bash
# Repository klonen
git clone https://github.com/<your-username>/studentenwerk-menu-ced-checker.git
cd studentenwerk-menu-ced-checker

# Virtuelle Umgebung erstellen und aktivieren
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt
# oder:
pip install requests openpyxl colorama
```

**Python 3.12+** erforderlich.

## Verwendung

### Tagescheck (Konsolenausgabe)

```bash
# Heute, Standard-Modus (aus settings.json)
python main.py

# Bestimmtes Datum
python main.py --date 2026-03-24

# Colitis ulcerosa Modus
python main.py --mode colitis

# Kombiniert
python main.py -d 2026-03-24 -m colitis
```

### Zeitraum-Report (xlsx-Export)

```bash
# Aktuelle Woche (Mo–Fr)
python main.py --from 2026-03-23 --to 2026-03-27

# Ganzer Monat, Colitis-Modus
python main.py --from 2026-03-01 --to 2026-03-31 -m colitis

# Eigener Dateiname
python main.py --from 2026-03-23 --to 2026-03-25 -o mein_report.xlsx
```

Der Report enthält drei Blätter:
- **Detailübersicht** — Jedes Gericht pro Tag/Mensa mit Note, Score, Preis, Nährwerten, Tags, Positiva und Warnungen
- **Tagesübersicht** — Bestes Gericht pro Tag, Anzahl verträgliche/ausgeschlossene Gerichte
- **Statistik** — Notenverteilung, häufigste Warnungen, Top-10-Gerichte, Statistik pro Mensa

## Konfiguration

### `config/settings.json`

Basis-URLs, Mensen und Standard-Krankheitsmodus:

```json
{
  "base_url": "https://sls.swo.bayern",
  "api_path": "/api/meals",
  "locations": [
    {"name": "hauptmensa-bayreuth", "label": "Hauptmensa", "categories": ["main"], "web_url": "https://sls.swo.bayern/hauptmensa-bayreuth"},
    {"name": "frischraum-bayreuth", "label": "Frischraum", "categories": ["main"], "web_url": "https://sls.swo.bayern/frischraum-bayreuth"},
    {"name": "salatbar-bayreuth", "label": "Salatbar", "categories": ["salad"], "web_url": "https://sls.swo.bayern/salatbar-bayreuth"}
  ],
  "disease_mode": "crohn"
}
```

Weitere Mensen oder Standorte können hier ergänzt werden.

### `config/allergene_zusatzstoffe.xlsx`

Bewertung aller Allergene und Zusatzstoffe (basierend auf der offiziellen Allergeneliste des Studierendenwerks):

| Code | Beschreibung | Bewertung_Crohn | Bewertung_Colitis |
|------|-------------|-----------------|-------------------|
| 1 | mit Farbstoff | vermeiden | vermeiden |
| a1 | Weizengluten | vermeiden | akzeptabel |
| g | Milch und Erzeugnisse | vermeiden | akzeptabel |
| ... | ... | ... | ... |

Mögliche Werte: `ausgeschlossen`, `vermeiden`, `akzeptabel`

### `config/nahrungsmittel.xlsx`

Bewertung von Nahrungsmitteln und Legende-Tags (Schwein, Vegan, etc.) sowie individuelle Zutaten:

| Nahrungsmittel | Bewertung_Crohn | Bewertung_Colitis |
|---------------|-----------------|-------------------|
| Schwein | vermeiden | vermeiden |
| Geflügel | empfohlen | empfohlen |
| Chili | ausgeschlossen | ausgeschlossen |
| Kartoffel | empfohlen | empfohlen |
| ... | ... | ... |

Mögliche Werte: `ausgeschlossen`, `vermeiden`, `akzeptabel`, `empfohlen`

Eigene Einträge (z.B. `Gurke`, `Tomate`, `Curry`) können jederzeit ergänzt werden — das Tool prüft den Gerichttitel auf diese Schlüsselwörter.

## Bewertungsalgorithmus

1. Jedes Gericht startet mit **Score 10**
2. **Allergen-Codes** des Gerichts werden gegen `allergene_zusatzstoffe.xlsx` geprüft:
   - `ausgeschlossen` → Score 0, Gericht markiert
   - `vermeiden` → Score −2, Warnung
3. **Legende-Tags** (Schwein, Vegan, Geflügel, etc.) und **Schlüsselwörter im Titel** werden gegen `nahrungsmittel.xlsx` geprüft:
   - `ausgeschlossen` → Score 0
   - `vermeiden` → Score −2
   - `empfohlen` → Score +1
4. Score wird auf 0–10 begrenzt und in Note A–F umgewandelt

## Projektstruktur

```
studentenwerk-menu-ced-checker/
├── main.py                        # CLI-Einstiegspunkt
├── ced_checker/
│   ├── __init__.py
│   ├── api.py                     # API-Abruf (Studierendenwerk)
│   ├── models.py                  # Datenklassen (Meal, MealRating)
│   ├── config_loader.py           # xlsx/JSON-Konfiguration laden
│   ├── analyzer.py                # CED-Verträglichkeitsanalyse
│   ├── output.py                  # Farbige Konsolenausgabe
│   └── report.py                  # xlsx-Zeitraum-Reports
├── config/
│   ├── settings.json              # URLs, Mensen, Modus
│   ├── allergene_zusatzstoffe.xlsx # Allergen-Bewertungen
│   └── nahrungsmittel.xlsx        # Nahrungsmittel-Bewertungen
└── pyproject.toml
```

## Datenquelle

Die Speisepläne werden über die interne API des [Studierendenwerks Oberfranken](https://sls.swo.bayern) abgerufen (`POST /api/meals`). Es werden nur öffentlich zugängliche Daten gelesen.

## Hinweis

Dieses Tool ersetzt keine ärztliche Beratung. Die voreingestellten Bewertungen basieren auf allgemeinen Ernährungsempfehlungen bei CED und sollten individuell angepasst werden. Jeder Krankheitsverlauf ist unterschiedlich.

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
