**Arbeitsverzeichnis:** `/Users/daniel/Work/danieldeusing/morning-briefs/daniel` — `cd` dorthin als allerersten Schritt; alle Pfade unten sind relativ zu diesem Root.

# Tiefe Recherche & gezieltes Denken (PFLICHT)
**Denke tief, aber gezielt:** ausführliches Nachdenken („extended thinking") für die schweren Teile — Story-Auswahl, Quellen-Cross-Check, Auflösung von Quellen-Widersprüchen, Prognosen/Szenarien, ELI5-Framing — **nicht** für HTML-Gerüst, Tabellen-Befüllung oder Boilerplate. Daniel verlässt sich auf dieses Briefing als verlässliche, faktentreue Tages-Lektüre. Denke gründlich vor dem Schreiben; prüfe Quellen, hinterfrage Zahlen, rechne Zeitzonen konkret nach.

**Recherche-Disziplin aus `docs/CROSS_CUTTING.md` § 0 STRIKT befolgen:**
- **Jede Zahl live fetchen** — Rennergebnisse, Rundenzeiten, Startaufstellungen, Fahrer- UND Konstrukteurs-/Hersteller-Punkte, Quali-Abstände, Reifen-/Strafen-Details.
- **Niemals aus dem Modell-Gedächtnis schätzen.** Die Saison 2026 ist das große F1-Reglement-Reset-Jahr (neue Chassis + Power Units, neue Teams Audi/Cadillac) — die Kräfteverhältnisse weichen stark von älterem Wissen ab. Was du „weißt", ist vermutlich veraltet. **Alles gegen aktuelle, datierte Quellen prüfen.**
- **Cross-Check** bei wichtigen Zahlen: mindestens zwei unabhängige Quellen (z. B. formula1.com + motorsport.com). Widersprüche explizit im Brief flaggen statt eine Variante stillschweigend zu wählen.
- **Timestamp pro Zahl** (Quelle + Datum): „F1-Fahrerwertung, formula1.com, Stand 20.05.2026" / „FIA-WEC-Herstellerwertung nach Spa, fiawec.com".

# Searchable Content Structure
Read `docs/CROSS_CUTTING.md` §0-5, `docs/FORMAT.md`, `docs/COMPONENTS.md`. Study `public/football/de/<latest>.html` as the closest sibling (same full-table discipline, dual-timezone handling, honest fallback tiers).

Body class `cat-motorsport`. Mandatory standings tables (F1 drivers + constructors, WEC manufacturers). Timeline of upcoming sessions/races. Deep dives in body grid (3-col or 2-col).

# Timezone Discipline (PFLICHT)
Daniel reads in Ribeirão Claro/PR (BRT, UTC-3). Every F1/WEC session — Practice, Quali, Sprint, Race — in **both** zones: MESZ (Europe summer, UTC+2) + BRT. Example: „16:00 BRT / 21:00 MESZ". Compute concretely; never guess.
