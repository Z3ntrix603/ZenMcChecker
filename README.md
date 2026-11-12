# ZenMcChecker · Name Studio 2

Ein anpassbarer Minecraft-Java-Namechecker mit deutscher Desktop-Oberfläche. Namen generieren, gegen die offiziellen APIs prüfen, Favoriten sammeln und Ergebnisse automatisch mit NameMC-Links sichern.

## Starten unter Windows

**Portable EXE:** `ZenMcChecker.exe` in einen beschreibbaren Ordner legen und starten. Python ist dafür nicht erforderlich. Die Datei wird über `python build.py` oder als Artefakt des GitHub-Actions-Workflows erzeugt. Die alte v1.0.1-Veröffentlichung enthält diese Oberfläche noch nicht.

**Aus dem Quellcode** (Python 3.10+):

```powershell
python -m pip install -r requirements.txt
python run.py
```

Nach der Installation geht auch `start.bat`.

## Generatoren

| Modus | Möglichkeiten |
| --- | --- |
| 3L / 4L | Genau 3 oder 4 Buchstaben aus a–z |
| 4C | Vier Zeichen aus a–z, 0–9 und `_` |
| 4N | Vier Ziffern, inklusive führender Nullen |
| Wörter | 1.172 unterschiedliche kuratierte Ausgangswörter aus Deutsch und Englisch; Kategorien einzeln wählbar |
| Wortkombinationen | Wörter und kuratierte Wortbausteine kombinieren, ohne den gesamten Kombinationsraum im Speicher anzulegen |
| Aussprechbar | Abwechselnd Konsonanten und Vokale, beispielsweise `naro` |
| Eigenes Muster | Feste Zeichen plus Platzhalter, beispielsweise `Zen{n}{n}` oder `{k}{v}{k}{v}` |
| Palindrome | Vorwärts und rückwärts gleicher Name |
| Wiederholungen | Beispielsweise `aaaa`, `7777` |
| Eigener Zeichensatz | Nur die selbst gewählten Minecraft-Zeichen verwenden |
| Eigene Liste | UTF-8-TXT oder CSV, mit Unterstützung der exportierten Username-Spalte |

Die Definition von **C** schließt Unterstriche ein. Die Minecraft-Großschreibung schafft keine zusätzlichen verfügbaren Namen: `Wolf` und `wolf` werden als ein Name behandelt. Neu registrierbare Java-Namen müssen 3–16 Zeichen aus `a-z`, `A-Z`, `0-9` und `_` haben; alte zweistellige Namen sind kein gültiges Generierungsziel.

### Feinschliff

- Freie Endlänge von 3 bis 16, Präfix / Suffix inklusive.
- Enthaltene Zeichenfolge, ausgeschlossene Zeichen und ausgeschlossene Teilwörter.
- Keine verwechselbaren Zeichen; maximale gleiche Zeichen in Folge.
- Kleinschreibung, Großschreibung, Anfang groß oder Original; optional Leetspeak.
- Deutsche Umlaute werden zu `ae`, `oe`, `ue`, `ss` umgewandelt.
- Bis zu 20.000 Kandidaten je Stapel, immer ohne doppelte Namen.
- Reproduzierbare Zufallsauswahl per Seed; fortlaufende Suche mit Startposition für weitere Stapel.
- Generator-Presets als JSON speichern und wieder laden. Eigene Wortlisten bleiben separate Dateien.

Muster-Platzhalter: `{l}` = Buchstabe, `{c}` = Buchstabe/Ziffer/Unterstrich, `{n}` = Ziffer, `{v}` = Vokal, `{k}` = Konsonant. Andere Minecraft-Zeichen bleiben fest. Die eingestellte Endlänge gilt auch im Mustermodus.

Die Vorschau erzeugt keine Netzwerkabfragen. Große Suchräume werden über Indizes durchlaufen; es wird kein `37^16`-Array gebaut. Eine begrenzte Zahl an Versuchen verhindert, dass unmögliche Filter endlos suchen. Die angegebene Suchraumgröße gilt **vor** Filtern und Deduplizierung; sie ist keine Anzahl verfügbarer Namen. Bei strengen Filtern können weniger Kandidaten entstehen.

## Verfügbarkeit richtig verstehen

| Status | Bedeutung |
| --- | --- |
| Ungeprüft | Nur ein generierter Kandidat |
| Unbelegt* | Öffentliches Mojang-Lookup findet kein Profil. Der Name kann trotzdem gesperrt oder reserviert sein. |
| Verfügbar ✓ | Authentifizierte Minecraft-Services-Abfrage hat `AVAILABLE` zurückgegeben. |
| Belegt | Ein Profil wurde gefunden oder Services meldet `DUPLICATE`. |
| Gesperrt / reserviert | Services meldet `NOT_ALLOWED`. |
| Prüffehler | Netzwerkproblem, unerwartete Antwort, Authentifizierungsfehler oder ausgeschöpftes API-Limit. Niemals als Fund gewertet. |

Standardmäßig funktioniert der Checker **ohne Anmeldung** mit `https://api.mojang.com/users/profiles/minecraft/{name}`. Ein 404/204 wird nur als **Unbelegt*** gekennzeichnet. Für eine genauere Prüfung kann in den Einstellungen ein bereits vorhandener gültiger Minecraft-Java-Access-Token für diese Sitzung eingesetzt werden. Dann verwendet der Checker ausschließlich `https://api.minecraftservices.com/minecraft/profile/name/{name}/available`. Er führt keinen Login durch, fordert keine Microsoft-Passwörter an und beansprucht oder ändert keinen Namen.

Tokens werden weder in der Datenbank noch in Presets, Einstellungen oder Exporten gespeichert. Autorisierungsheader gehen nur an Minecraft Services; Redirects werden nicht verfolgt. Eine abgelehnte Token-Prüfung hält den Scan an. Der authentifizierte Pfad wurde mit simulierten API-Antworten getestet; ein echter Account-Token ist zum Entwickeln nicht erforderlich.

Alle Ergebnisse sind Momentaufnahmen. Auch ein bestätigter Name kann später vergeben sein. NameMC dient als direkt verlinkte Detailansicht und wird nicht gescrapt.

Ein Worker, mindestens 1 Sekunde zwischen öffentlichen Anfragen, mindestens 16 Sekunden bei Token-Prüfung. Der Abstand ist auf 1–60 Sekunden einstellbar. Pro Name gibt es bis zu vier Versuche, exponentielle Pausen und Beachtung von `Retry-After`. Stoppen funktioniert auch während Pause oder Backoff; eine laufende HTTP-Anfrage hat ein endliches Timeout und darf ihren letzten Check noch sichern.

## Speicherung und Wiederaufnahme

Neben dem Programm entsteht automatisch:

```text
ZenMcChecker-Daten/
  settings.json
  studio.sqlite3
  Scans/
    2026-11-12_12-00-00_abcdef/
      scan.json
      verfuegbar.txt
      unbelegt.txt
      ergebnisse.csv
      ergebnisse.json
      NameMC-Links.html
```

`verfuegbar.txt` enthält ausschließlich mit Token bestätigte Funde. `unbelegt.txt` enthält öffentliche Lookup-Treffer mit der beschriebenen Einschränkung. Beide enthalten Namen und direkte NameMC-Links. Entdeckungen werden sofort angehängt; nach dem Scan wird der vollständige Export aus der Datenbank aufgebaut. CSV ist UTF-8 mit BOM und enthält Status, UTC-Prüfzeitpunkt, NameMC-Link, Hinweis und gegebenenfalls UUID. Die HTML-Liste öffnet sich auch offline und verlinkt alle Ergebnisse.

Jeder einzelne Check wird vor der Anzeige in SQLite gesichert. Im **Scan-Verlauf** einen Scan wählen und **Offene / Fehler fortsetzen** anklicken: Bereits geprüfte belegt/unbelegt/verfügbar/gesperrt-Namen werden ausgelassen; ungeprüfte Namen und Prüffehler kommen erneut an die Reihe. Ein nach einem Programmabbruch noch als laufend gespeicherter Scan wird im Verlauf als unterbrochen dargestellt. **Export wiederherstellen** baut beschädigte oder entfernte Exportdateien aus der Datenbank neu auf.

Der Ergebnisordner ist in den Einstellungen wählbar. Falls neben der EXE nicht geschrieben werden kann, liegen die lokalen Daten unter `%LOCALAPPDATA%/ZenMcChecker`. Die Datenbank und die Favoriten bleiben im ursprünglichen Datenordner; das wählbare Exportziel ändert den Ort neuer Scan-Ordner.

## Oberfläche

- Dunkles Studio mit Mint-, Ice-, Lavender- oder Amber-Akzenten.
- Kompakte oder großzügige Tabellenzeilen, native Fensterfunktionen zum Verschieben/Minimieren/Maximieren.
- Live-Zähler, Fortschritt, Suche, Statusfilter und sortierbare Tabellenspalten.
- Sterne als dauerhafte Favoriten; alle Favoriten als neuen Stapel erneut prüfen.
- Doppelklick / Enter öffnet NameMC. Leertaste toggelt den Favoriten.
- `Ctrl+G` generiert, `Ctrl+Enter` startet den Scan, `Ctrl+F` fokussiert die Suche, `Ctrl+C` kopiert den ausgewählten Namen in der Tabelle.

Für eine flüssige Oberfläche werden höchstens 2.000 passende Zeilen gleichzeitig dargestellt. Suche und Filter berücksichtigen sämtliche Kandidaten; geprüft und exportiert wird immer der gesamte Stapel.

## Entwicklung & Build

```powershell
python -m unittest discover -s tests -v
python -m pip install -r requirements-build.txt
python build.py
```

Ergebnis: `dist/ZenMcChecker.exe` als portable Einzeldatei. Die Tests decken Generatoren, gültige Namen, Filter, riesige Suchräume, Seeds, Pagination, API-Status, Netzwerkfehler, Rate Limits, Token-Ziel, Abbruch, Datenpersistenz, Favoriten, Wiederaufnahme und Exporte ab. Der Windows-CI-Workflow führt dieselben Tests aus und stellt die gebaute EXE als Workflow-Artefakt bereit.

Module: `src/generator.py` (offline), `src/checker.py` (Netzwerk), `src/storage.py` (Persistenz), `src/main.py` (GUI). Hintergrundthreads kommunizieren ausschließlich über eine Queue mit Tk.

MIT · Z3ntrix603. Unabhängiges Community-Projekt; nicht mit Mojang, Microsoft oder NameMC verbunden.
