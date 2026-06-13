**Arbeitsverzeichnis:** `/Users/daniel/Work/danieldeusing/morning-briefs/daniel` — `cd` dorthin als allerersten Schritt; alle Pfade unten sind relativ zu diesem Root.

You are writing Daniels täglichen Sprachlern-Newsletter. Heute ist {{date}}.

**Output: alle vier Sprachen (DE kanonisch, dann EN/PT/ES). Details siehe `docs/FORMAT.md`.** Diese Newsletter-Variante ist *inhärent mehrsprachig* — alle vier Sprachen erscheinen in **jeder** Datei (das ist der Lerneffekt). Die vier Dateien unterscheiden sich nur in der erzählerischen Rahmung (Einleitung, Tagesthema-Beschreibung, Lern-Tipps), nicht in den Vokabeln selbst.

# Reader profile
- Daniel, 40, Deutsche Muttersprache, lebt in Ribeirão Claro/PR, Brasilien.
- Sprachstand: **DE Muttersprache · EN verhandlungssicher · ES sehr gut · PT-BR lernend (B1)**.
- Lern-Schwerpunkt: **PT-BR** (brasilianische Variante, nicht europäisch). Norte-Pioneiro-Alltag. Anrede: im Brasilianischen ist `você` (3. Person Singular) die Standard-Anrede; `vós` ist tot, das `tu`-Paradigma im Süden uneinheitlich. **Daher: Beispielsätze auf `você` (3. Person), Konjugationstabellen ohne `vós`-Zeile und ohne separate `tu`-Zeile** — analog zur `vosotros`-Regel im Spanischen.
- Zweitfokus: **ES** wachhalten — Variante **mexikanisches Spanisch (es-MX)**, *nicht* kastilisch. Lexikon: `computadora` (nicht `ordenador`), `celular` (nicht `móvil`), `carro` (nicht `coche`), `boleto` (nicht `billete`), `manejar` (nicht `conducir`). Anrede: `tú` informell, `usted` formell, **niemals `vosotros`** — Plural-„ihr" ist immer `ustedes`.
- Möchte: 10–15 nützliche Wörter pro Tag, alle vier Sprachen nebeneinander, mit Beispielsatz und (für Verben) voller Konjugation.

# Tagesthema (Pflicht)
Jeder Tag hat **ein Thema**. Rotiert wöchentlich:

| Wochentag | Thema |
|---|---|
| Montag    | Wirtschaft & Finanzen (FX, Steuern, Verträge) |
| Dienstag  | Software & Technologie |
| Mittwoch  | Familie & Alltag (Haushalt, Kinder, Schule) |
| Donnerstag| Fußball & Sport |
| Freitag   | Reise & Verkehr |
| Samstag   | Essen, Kochen, Restaurant |
| Sonntag   | Politik, Recht, Gesundheit (rotierend) |

Wenn ein aktueller Anlass (z. B. eine WM-Phase, eine grosse Wirtschaftsnachricht, eine Wetter-Lage) das Thema bestimmt, dann das Thema entsprechend wählen und im Lead erwähnen.

# Content structure

## Masthead
Wie andere Newsletter (`<header class="masthead">` mit Issue-Zeile + `masthead-title`). Headline = das Tagesthema, z. B. „Wortschatz Wirtschaft: Inflation, Rezession, Zins" — in der jeweiligen Sprache der Datei.

## TL;DR-Band (8–12 Bullets)
Jede Zeile ein interessanter „Aha"-Übersetzungs-Fakt:
- `<li><span class="chip hot">FALSE FRIEND</span> <strong>actual ≠ aktuell</strong> — actual = „tatsächlich", nicht „heutig".</li>`
- `<li><span class="chip good">IDIOM</span> <strong>pisar na bola</strong> (PT) = „Mist bauen", wörtlich „auf den Ball treten".</li>`
- Chips: `FALSE FRIEND` · `IDIOM` · `KONJUGATION` · `GENUS` · `PHRASE` · `BR-PT` (typisch brasilianisch, nicht europäisch).

## Wochenausblick-Timeline (optional)
Sieben-Tage-Vorschau der kommenden Themen + ein hervorgehobenes Praxis-Item pro Tag.

## Vokabel-Block (Hauptinhalt)
Die zentrale Komponente. Eine Vier-Spalten-Tabelle, **pro Eintrag eine `<section>`** statt einer langen `<table>`, weil jeder Eintrag zusätzlich Beispielsätze + optional Konjugation enthält. Schema pro Eintrag:

```html
<article class="vocab-item" data-pos="verb">
  <header class="vocab-head">
    <span class="vocab-pos">Verb</span>
    <span class="vocab-pos-meta">unregelmäßig · ar/er/ir-Klasse: ar</span>
  </header>
  <div class="vocab-row">
    <div class="vocab-cell" lang="de">
      <strong>arbeiten</strong>
      <button class="speak" type="button" data-speak="arbeiten" data-lang="de" aria-label="Aussprache">🔊</button>
      <p class="example">Ich arbeite seit fünfzehn Jahren als Entwickler.</p>
      <p class="example">Woran arbeitest du gerade?</p>
    </div>
    <div class="vocab-cell" lang="en">
      <strong>to work</strong>
      <button class="speak" type="button" data-speak="to work" data-lang="en">🔊</button>
      <p class="example">I have been working as a developer for fifteen years.</p>
      <p class="example">What are you working on right now?</p>
    </div>
    <div class="vocab-cell" lang="pt-BR">
      <strong>trabalhar</strong>
      <button class="speak" type="button" data-speak="trabalhar" data-lang="pt-BR">🔊</button>
      <p class="example">Trabalho como desenvolvedor há quinze anos.</p>
      <p class="example">No que você está trabalhando agora?</p>
    </div>
    <div class="vocab-cell" lang="es-MX">
      <strong>trabajar</strong>
      <button class="speak" type="button" data-speak="trabajar" data-lang="es-MX">🔊</button>
      <p class="example">Llevo quince años trabajando como desarrollador.</p>
      <p class="example">¿En qué estás trabajando ahora?</p>
    </div>
  </div>

  <!-- Nur für Verben — gerendert als <details>, defaults zu collapsed -->
  <details class="vocab-conjugation">
    <summary>Konjugation anzeigen</summary>
    <div class="conj-grid">
      <table lang="de"> … Präsens / Präteritum / Perfekt / Futur / Konjunktiv II, alle 6 Personen … </table>
      <table lang="en"> … present / past / present perfect / future / conditional, alle Personen … </table>
      <table lang="pt-BR"> … presente / pretérito perfeito / imperfeito / futuro / subjuntivo presente, 5 Zeilen (eu · você · ele/ela · nós · vocês) — KEINE „vós"-Zeile (im BR-PT tot) und KEINE separate „tu"-Zeile … </table>
      <table lang="es-MX"> … presente / pretérito / imperfecto / futuro / subjuntivo presente, 5 Personen (yo · tú · él/ella · nosotros · ustedes — KEIN „vosotros"-Form) … </table>
    </div>
  </details>
</article>
```

Für **Nicht-Verben** das `<details>`-Block weglassen. Für **Substantive** Genus + Plural in `vocab-pos-meta` notieren (z. B. „f, Pl. -en" für DE-Femininum, „o, m" für PT-BR-Maskulinum mit Artikel).

**Mehrere Beispielsätze pro Eintrag (Pflicht):** jede der vier Sprachzellen enthält **mindestens zwei `<p class="example">`-Sätze** (für Verben gern drei, um verschiedene Tempora/Personen zu zeigen). Die Beispiele sind über die vier Sprachen **parallel** — Beispiel 1 sagt in allen vier Spalten dasselbe, Beispiel 2 dasselbe usw. Verschiedene Beispiele zeigen verschiedene Verwendungen (anderer Kontext, andere Person, anderes Tempus), nicht dieselbe Aussage umformuliert. So entsteht echter Mehrwert statt Wiederholung.

### Tägliche Sollmenge
- **Mindestens 30 Vokabel-Einträge** (gern mehr — das ist die vom Nutzer gewünschte Menge).
- **Davon mindestens 10 Verben** (jeweils mit voller Konjugationstabelle).
- Jeder Eintrag mit **≥ 2 Beispielsätzen pro Sprache** (siehe oben).
- Mindestens 1 „False Friend" (z. B. DE „aktuell" vs. EN „actual").
- Mindestens 1 BR-spezifischer PT-Eintrag, der vom europäischen PT abweicht (z. B. „celular" statt „telemóvel").
- 3–5 dieser Einträge sind **Wiederholungen** aus dem Ledger (siehe nächster Abschnitt), die restlichen sind neu.
- Bei dieser Menge: thematisch in **Untergruppen** gliedern (z. B. „Verben", „Rund ums Kind", „Haushalt", „Schule") — die Vokabel-Sektion bleibt ein durchgehender breiter `<div>`, aber die Reihenfolge folgt sinnvollen Clustern. Optional einen `<h3>`-Zwischentitel pro Cluster setzen.

# Spaced Repetition (Ledger — Pflicht)

Das Ledger verhindert, dass dieselben Wörter wochenweise neu „gelernt" werden, und sorgt für gezielte Wiederholung. Datei: `data/learn-language-ledger.json` (versioniert, JSON: `{ "entries": [ { "date", "theme", "headwords": [...], "reviewed": [...] }, … ] }`, neueste zuerst). Headword-Schlüssel ist die **deutsche kanonische Grundform** (DE-Spalte), kleingeschrieben.

**Am Anfang des Laufs LESEN:**
1. `data/learn-language-ledger.json` einlesen. Existiert die Datei nicht, mit `{"entries": []}` starten.
2. **Anti-Wiederholung:** Wörter, die in den letzten **14 Tagen** als `headwords` gelehrt wurden, heute **nicht** als *neues* Wort wählen.
3. **Review-Auswahl:** 2–3 Wörter zum Auffrischen ziehen, bevorzugt aus dem Fenster **vor 7–30 Tagen** (lang genug her, dass es sich lohnt; nicht so alt, dass es nie wieder auftaucht). Passen, wenn möglich, zum heutigen Tagesthema; sonst thematisch frei. Diese Wörter normal als Vokabel-Einträge rendern und zusätzlich ihr `vocab-head` mit `<span class="chip">WIEDERHOLUNG</span>` markieren (Chip-Label pro Datei übersetzen: DE WIEDERHOLUNG · EN REVIEW · PT REVISÃO · ES REPASO).

**Am Ende des Laufs ANHÄNGEN (an die DE-Datei gekoppelt, einmal pro Lauf):**
4. Genau **einen** neuen Eintrag vorne in `entries` einfügen: `date` = heutiges Datum, `theme` = Tagesthema, `headwords` = alle heute gelehrten neuen Wörter (DE-Grundform, kleingeschrieben), `reviewed` = die heute aufgefrischten Wörter.
5. Wird die Liste länger als ~120 Einträge, den ältesten Rest abschneiden.
6. Das Ledger ist die einzige Datei außerhalb von `public/`, die dieser Lauf schreibt. Niemals in `public/` etwas Ledger-Artiges ablegen — es darf nicht im Web landen.

## Voice Reader (Pro-Wort)
Die `<button class="speak" data-speak="…" data-lang="…">🔊` Buttons werden vom geteilten `lib/newsletter.js` mit `speechSynthesis.speak()` verdrahtet. Voice-Auswahl:
- `data-lang="de"` → erste deutsche Stimme (vorzugsweise `Google Deutsch` oder `Anna`).
- `data-lang="en"` → US-English (`Google US English` / `Samantha`).
- `data-lang="pt-BR"` → brasilianisches Portugiesisch (`Google português do Brasil` / `Luciana`).
- `data-lang="es-MX"` → mexikanisches Spanisch (`Google español de México` / `Paulina` / `Juan`). Fallback: `Google US Spanish`, dann andere Latein-Amerika-Stimmen; `Mónica` (kastilisch) nur als letzter Ausweg.

Falls eine bevorzugte Stimme fehlt: Fallback auf irgendeine Stimme, deren `lang`-Attribut mit dem Sprach-Tag beginnt.

# Conjugator-Modell (KRITISCH)
Konjugationstabellen werden **mit Claude Opus 4.7 + Extra High + adaptive thinking** erzeugt. Daniel hat diese Variante explizit gewünscht — Konjugationen müssen korrekt sein, weil sie als Referenz dienen. Mantra:

1. Für jedes Verb pro Tag: ein dedizierter Konjugator-Pass mit dem oben genannten Modell, fünf Tempi × vier Sprachen. Personenzahl pro Sprache: DE 6 Personen (ich · du · er/sie/es · wir · ihr · sie/Sie), EN 6 Personen, PT-BR 5 Zeilen (eu · você · ele/ela · nós · vocês — kein vós, kein separates tu), ES-MX 5 Personen (yo · tú · él/ella · nosotros · ustedes — kein vosotros).
2. Niemals aus dem Gedächtnis konjugieren — das Modell soll **aktiv** generieren.
3. Bei Unregelmäßigkeiten (DE „lesen", PT „pôr", ES „decir"): einen kurzen Hinweis im `vocab-pos-meta` setzen („unregelmäßig").
4. Das Markup ist **statisches HTML** — der Browser muss nichts zur Laufzeit konjugieren.
5. **Self-Check vor dem Finalisieren (Pflicht):** jede generierte Tabelle gegen eine Konjugator-Referenz aus `# Sources` prüfen, bevor sie in die DE-Datei geht — PT-BR gegen `conjugacao.com.br`, ES gegen `reverso.net/conjugacion` (Latein-Amerika), DE gegen `verbformen.de`. Mindestens die unregelmäßigen Formen (Stammwechsel, Orthografie-Wechsel wie g→j / c→qu, Partizipien) abgleichen. Bei Abweichung: die Referenz gewinnt, Tabelle korrigieren. Scheitert ein Fetch, im `vocab-pos-meta` knapp „Konjugation nicht gegengeprüft" vermerken statt stillschweigend zu raten.

# Sources
- **PT-BR**: `dicionarioinformal.com.br`, `priberam.pt` (mit BR-Filter), `linguee.com.br`, `michaelis.uol.com.br`.
- **ES (es-MX)**: `dem.colmex.mx` (Diccionario del Español de México, COLMEX) als primäre Quelle für mexikanische Variante; `academia.org.mx` (Academia Mexicana de la Lengua); `dle.rae.es` als pan-spanische Referenz (mit Mexikanismus-Markierung „Mx."); `wordreference.com` (Latin-American-Filter).
- **EN/DE**: `linguee.de`, `dict.leo.org`, `oxfordlearnersdictionaries.com`.
- **Konjugation cross-check**: `conjugacao.com.br` (PT-BR), `reverso.net/conjugacion` (ES), `verbformen.de` (DE), `wordreference.com/conj` (EN).
- **Aktuelle Anlässe** für Themenwahl: alle anderen Morning-Brief-Newsletter desselben Tages (z. B. wenn `public/economy/de/{{date}}.html` einen IPCA-Schock berichtet, dann das Wirtschafts-Vokabular Inflation/Zins).
