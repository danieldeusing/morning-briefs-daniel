# Morning Brief — Cross-Cutting Editorial Principles

Gilt für alle Morning-Brief-Newsletter (außer `dashboard`, das nur das Manifest neu baut). Jeder Newsletter-Prompt verweist auf diese Datei am Anfang. Bei Konflikt: die per-Newsletter-Regel im jeweiligen Task-Prompt gewinnt.

## Themen-Abgrenzung & Dedup (zwischen den Newslettern)

Die acht Newsletter laufen unabhängig und ohne Wissen voneinander — sonst landet dieselbe Story am selben Tag in mehreren Briefs (z. B. eine KI-Keynote gleichzeitig in `software`, `ai-dev` und `ai-usecases`). Regeln:

- **Klare Reviere:**
  - `ai-dev` = KI fürs Programmieren (Coding-Modelle, Agent-Tools, Harnesses, MCP, IDE-Integrationen, Benchmarks, lokale LLM-Toolchains).
  - `ai-usecases` = angewandte KI in Wirtschaft/Industrie/Öffentlichkeit — **keine** Dev-Tools.
  - `software` = Nicht-KI-Software/IT (CVEs, Releases, Sprachen, Frameworks, Infra, Standards, Regulierung). KI-Modell- und Agent-Launches gehören NICHT hierher — höchstens deren Software-Engineering-Zweitwirkung (Supply-Chain, Tooling als Angriffsfläche, Lizenzen).
- **Verlinken statt duplizieren:** Ist eine Story primär das Revier eines anderen Newsletters, hier nur ein Satz + Verweis („Details im ai-dev-Brief"), nicht die volle Story.
- **Im Zweifel gewinnt das speziellere Revier**, die anderen verweisen darauf.

## 0. Vor jedem Lauf — Recherche-Disziplin (MUSS)

### Tiefe & Denken — gezielt, nicht pauschal
Das ist kein Standard-Newsletter, sondern Daniels Entscheidungs-Grundlage:
FX-Timing für reale Rechnungen, Karriere-Schritte, Familien-Planung,
Gesundheits-Alerts. **Setze ausführliches Nachdenken („extended thinking") dort
ein, wo es zählt** — Story-Auswahl, Quellen-Cross-Check, Auflösung von
Quellen-Widersprüchen, Prognosen/Szenarien, ELI5-Framing. **Verschwende es
NICHT** auf HTML-Gerüst, Tabellen-Befüllung, Übersetzungs-Mechanik oder
Boilerplate — das ist Token-Verschwendung ohne Qualitätsgewinn. Tiefe an den
schweren Stellen, zügig durch den Rest.

### Live-Daten Pflicht — keine Schätzungen
- **Zahlen IMMER aus aktuellen, datierten Quellen fetchen.** Niemals aus dem Modell-Gedächtnis schätzen. Gilt für FX-Kurse, Sport-Ergebnisse, Wetter, Rate-Listings, Tabellen-Stände, Bench-Scores, Krankheits-/Sicherheits-Alerts — alles Numerische.
- **Cross-Check** bei wichtigen Zahlen: mindestens zwei unabhängige Quellen. Differenzen >0,5 % bei FX oder offensichtliche Widersprüche bei anderen Daten explizit im Brief flaggen.
- **Quellen-Hierarchie:** Primär-/Offiziell-Quellen zuerst (Emittent, Behörde, IR-/Investor-Seite, offizielle Tabelle/Leaderboard), dann etablierte Fach-/Nachrichtenmedien, Blogs/Aggregatoren nur als letzte Stufe — und nie als alleinige Quelle für eine Zahl.
- **Timestamp** jeder Zahl: „ECB-Referenz, 14.05.2026 16:00 CET" oder „Boletim Epidemiológico PR, KW 19/2026". Ohne Timestamp keine Zahl.
- **Wenn ein Fetch scheitert**: NICHT raten. Explizit schreiben „Daten zu X heute nicht verfügbar; letzter verifizierter Stand: YY am ZZ.MM" und mit dem letzten verifizierten Wert weiterarbeiten.
- **Fallback-Leiter bei Block/403/Timeout:** Primärquelle nicht erreichbar → die im Task-Prompt (`# Sources`) hinterlegte Ausweichquelle nutzen, nicht sofort aufgeben. Bleibt alles blockiert, den letzten verifizierten Stand mit Datum nennen.
- **Visuals & Datenblöcke nur mit echten Werten:** Historische Reihen für Charts UND inline-JSON-Blöcke (z. B. `#fx-series`, `#bench-data`) live fetchen. Reihe nicht verfügbar → **Chart/Datenblock weglassen** statt mit Mock-/Platzhalter-Werten füllen (auch keine „ungefähr"-Werte in Sparkline-Serien). Lieber Lücke als falsche Zahl.

### Fetch-Ökonomie — so wenig wie nötig, so viel wie nötig
Jeder voll geladene `WebFetch` einer Seite kostet viele Tokens. Diszipliniert
fetchen, ohne an Qualität zu sparen:
- **Erst `WebSearch` (billige Snippets) zum Triagieren**, dann `WebFetch` nur die
  Seite(n), die du tatsächlich **zitieren** wirst. Keine Seite „auf Verdacht"
  voll laden.
- **Wert-liefernde Skills vor rohem Fetch:** `fx-snapshot`, `fetch-with-fallback`
  geben **Wert + Quelle + Sample-Datum** zurück statt einer ganzen Seite — nutze
  sie für einzelne Zahlen. Hat ein Skill die Zahl schon geliefert, nicht
  zusätzlich dieselbe Seite fetchen.
- **Weicher Deckel ~10–15 Fetches pro Kategorie.** Mehr braucht es selten; wenn
  doch, dann gezielt für die entscheidungs-treibenden Zahlen, nicht für den
  narrativen Long-Tail.
- **Quellen-Belege im Scratch festhalten** (`/tmp/brief-sources-<cat>-<date>.md`):
  pro Zahl ein kurzes wörtliches Snippet + URL + Datum. Das spart dem
  Fact-Checker das erneute Laden derselben Seite (er korroboriert die
  hoch-riskanten Zahlen trotzdem unabhängig).

### Konkretes für FX (economy)
- **EUR/BRL primary**: ECB-Referenzkurs (`ecb.europa.eu/.../eurofxref-graph-brl.en.html`) — täglicher Fix ~16:00 CET, AA-Qualität.
- **EUR/BRL Cross-Check** (mind. eine zusätzlich nennen): exchange-rates.org/converter/eur-brl ODER USD/BRL × EUR/USD-Cross aus TradingEconomics / BCB Ptax / Reuters.
- Wenn EUR/USD und USD/BRL einzeln verfügbar sind, EUR/BRL daraus rechnen und gegen ECB abgleichen — Differenz >0,5 % im Brief flaggen.
- **Wise NICHT als Quelle nutzen**. Das öffentliche Wise-Widget (`wise.com/.../eur-to-brl-rate`) cached aggressiv — mehrere Tage Stale-Werte wurden im Mai 2026 beobachtet (Widget zeigte 6,04 während die In-App-Rate bei 5,87 lag). Wenn Wise dennoch zitiert werden soll, dann als „Wise In-App-Rate (Daniel zitiert)" ohne URL.

### Konkretes für Sport (football)
- Spielstände + Tabellen: kicker.de oder bundesliga.com (DE), globoesporte.globo.com (BR), uefa.com (UCL). Stand immer mit Datum benennen.
- xG / Pressing-Stats: understat.com, fbref.com. Quelle + Datum nennen.

### Konkretes für Wetter (family)
- climatempo.com.br oder inmet.gov.br für Ribeirão Claro. CEMADEN für Warnungen. Timestamp pflicht.

## 1. Recherche nach Themen-Clustern (inline)

Im konsolidierten Routine-Modell schreibt **ein `brief-writer`-Sub-Agent pro
Kategorie** den Brief. Ein Sub-Agent **kann selbst keine Sub-Agenten spawnen** —
recherchiere also **inline**, nicht über weitere Agenten. (Recherche, die einen
eigenen Agenten braucht — z. B. `jobs-aggregator` — startet der Orchestrator
*vor* dem Writer und reicht das Ergebnis durch.)

Trotzdem nach Clustern arbeiten — das hält die Recherche fokussiert:
1. Themen-Cluster für heute identifizieren (z. B. economy: „FX-Spot & Charts",
   „Notenbanken", „BR-Fiskal", „US-Tape", „Sentiment & Positionierung").
2. Cluster nacheinander abarbeiten, Quellen-Hinweise aus der `# Sources`-Sektion
   des Kategorie-Specs nutzen, dabei die **Fetch-Ökonomie** (§ 0) einhalten.
3. Ergebnisse in den Brief gießen.

## 2. Twitter/X via fxtwitter.com

Twitter/X als Echtzeit-Signal nutzen. **Zugriff IMMER über `fxtwitter.com`** (twitter.com gibt für Crawler kein nutzbares HTML zurück):

- Profil: `https://fxtwitter.com/<handle>`
- Einzel-Post: `https://fxtwitter.com/<handle>/status/<id>`

Hashtag-/Stichwort-Suche per Crawl ist unzuverlässig — bevorzugt über bekannte Handles und über Posts, die von News-Aggregatoren zitiert werden.

Pro Newsletter ist eine kuratierte Handle-Liste in dessen `# Sources`-Sektion.

## 3. Visuals — nur wenn nützlich

HTML-Output erlaubt **inline SVG** und über CDN **Chart.js / Mermaid**. Einsetzen für:

- **Linien-/Bar-Charts** (Chart.js): Kurs-Verläufe, Rate-Trends, Vergleichswerte.
- **Sparklines** (inline SVG): Mini-Trends in Karten (Dashboard nutzt das schon).
- **Mermaid-Diagramme**: Kausalketten („A → B → C"), Ablaufdiagramme, Entscheidungsbäume.
- **Tabellen**: strukturierte Vergleiche (schon im Einsatz).

**Kein Pflicht-Ornament.** Wenn Text die Sache besser trägt, weglassen. Wenn ein Chart den Punkt in zwei Blicken erklärt statt in drei Absätzen, einbauen.

CDN-Skripte am Ende des HTML einbinden (siehe `docs/FORMAT.md` für die genaue Struktur):
- Chart.js: `https://cdn.jsdelivr.net/npm/chart.js`
- Mermaid: `https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js`

## 4. ELI5 — verständlich ohne Master-Abschluss in der Domäne

Daniel ist Software-Entwickler — **kein Banker, kein Healthcare-Experte, kein Pharma-Analyst, kein Bundesliga-Taktik-Coach**. Schreibe so, dass er ohne Master-Background in der jeweiligen Domäne versteht.

**Regel:** Beim ersten Auftauchen eines Fachbegriffs:
1. **Ein Satz Definition.**
2. **Ein Satz Real-World-Analogie**, die ein Kind versteht.
3. Dann der eigentliche News-Punkt.

Spätere Wiederholungen des Begriffs OK ohne Erklärung.

**Beispiele für die Übersetzung:**

- **„OIS-Spread komprimiert um 8 bps"** → „Banken wetten an ihren Future-Märkten gerade darauf, dass die nächsten Zinssenkungen geringer ausfallen als gestern erwartet — das hat sich um 8 Basispunkte verschoben."
- **„Inverted Yield Curve"** → „Stell dir vor, der Bäcker verlangt für ein Brot, das nächstes Jahr fertig wird, weniger als für eines heute. Das wirkt seltsam — und passiert nur, wenn alle erwarten, dass Preise demnächst fallen. Im Anleihen-Markt: kurze Laufzeiten zahlen mehr als lange — klassisches Rezessions-Signal."
- **„Carry Trade BRL"** → „Geld leihen wo's billig ist (z. B. Japan), in Brasilien zu hohen Zinsen anlegen. Solange der BRL-Kurs nicht einbricht, ist der Zinsunterschied dein Profit. Wenn der Real fällt, ist die Party vorbei."
- **„Quantization (AI-Modell)"** → „Wie ein Foto auf JPG komprimieren: bisschen Qualität verloren, aber das Modell passt in viel weniger Speicher und läuft schneller. Q4 = 4 Bits pro Gewicht statt 16."
- **„xG = 0.23"** → „Wahrscheinlichkeits-Rechnung: aus dieser Schussposition hätten im Schnitt 23 von 100 Spielern getroffen. Egal ob Tor oder Fehlschuss — gemessen wird die Qualität der Chance."
- **„RAG"** → „Statt das KI-Modell selbst die Antwort halluzinieren zu lassen, sucht das System zuerst in einer Dokumenten-Datenbank nach passenden Stellen und gibt die dem Modell als Kontext mit. Ergebnis: das Modell zitiert reale Quellen statt zu raten."
- **„Pressing-Höhe (Fußball)"** → „Wie weit vorne im Feld eine Mannschaft den Gegner attackiert. Hoch = direkt beim Torhüter; tief = erst kurz vor dem eigenen Strafraum. Hohes Pressing kostet Kondition, gibt aber schnelle Ballgewinne nah am gegnerischen Tor."
- **„NTN-B Real-Yield"** → „Brasilianische Anleihe, die Inflation rauspuffert: du bekommst garantiert IPCA + X % drauf, egal wie hoch die Inflation springt. Der X-Wert (Real-Yield) zeigt, wie viel echten Wertzuwachs der Markt vom Staat verlangt."

**Wichtig:** Dies steht **nicht im Widerspruch** zur „opinionated voice"-Vorgabe. Der Ton bleibt klar und meinungsstark, nur die Wörter sind nahbar. **Tiefe ohne Hürde.**

## 5. Output — content-only HTML, kein Inline-CSS/JS, kein E-Mail-Draft

Newsletter-Output ist **eine einzige HTML-Datei** pro Newsletter pro Tag:

- `public/<category>/<lang>/{{YYYY-MM-DD}}.html` (relativ zum Projekt-Root).

Die Datei ist **content-only**:
- `<link rel="stylesheet" href="../../lib/styles.css">` für ALLE Styles (Scaffold + Components).
- `<script defer src="../../lib/newsletter.js">` für ALLE Interaktionen (Auto-Init).
- Optional `<script src="…cdn…/chart.js">` / Mermaid CDN in `<head>` nur wenn ein Component es braucht.
- `<body class="cat-{category}">` setzt den Accent-Farbton.
- **Kein `<style>` im Body. Kein inline `<script>` im Body** (Ausnahme: `<script type="application/json" id="…">` für Datenblöcke wie `#fx-series` oder `#bench-data` am Body-Ende).

**Keine Markdown-Twin** mehr (Gmail-Zustellweg entfernt). **Keine Gmail-Draft-Erzeugung.**

Die HTML ist ein vollständiges standalone-Dokument (`<!DOCTYPE html>` bis `</html>`), wird vom Dashboard per `<iframe>` eingebunden.

Siehe `docs/template.html` für das Skeleton, `docs/COMPONENTS.md` für die HTML-Fragmente, `docs/FORMAT.md` für die Assembly-Regeln.
