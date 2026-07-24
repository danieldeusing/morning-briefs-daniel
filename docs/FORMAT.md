# Shared format spec for all newsletters

Every newsletter SKILL in this folder follows the spec below. Topic SKILLs (`SKILL-economy.md`, `SKILL-software.md`, etc.) reference this file rather than duplicate it.

## Output languages
Every brief is published in **four languages**, in this order:

1. **German (`de`)** — canonical. Research, judgement, draft pass live here. All numeric work, source picking, story selection happens in German first.
2. **English (`en`)** — US-English translation of the DE draft.
3. **Portuguese (`pt`)** — Brazilian Portuguese (pt-BR) translation.
4. **Spanish (`es`)** — **Mexican Spanish (es-MX)** translation. Lexicon: `computadora` (not `ordenador`), `celular` (not `móvil`), `carro` (not `coche`), `boleto` (not `billete`), `manejar` (not `conducir`). Grammar: tuteo for informal address (`tú`), never `vosotros` — use `ustedes` for plural-you. No Castilian-only verb forms (no `vosotros tenéis`; use `ustedes tienen`). Latin-American date and number conventions.

Translate the **entire visible document**: narrative prose, headings, UI labels, callout text, chip labels, `<title>`, `aria-label`, image alt, the timeline rows, the dashboard cards. Keep these **unchanged** across all four languages:

- Proper nouns (institutions, product names, model names, CVE IDs, ticker symbols, person names).
- HTML structure, CSS classes, `data-*` attributes, inline JSON data blocks, source URLs.
- Numeric values — only the *separator format* changes (see below).

### Per-locale formatting
| Locale | Decimal sep. | Thousand sep. | Currency style | `<html lang>` |
|---|---|---|---|---|
| `de` | comma `5,77` | space or dot `1 234` | `5,77 €` | `de` |
| `en` | dot `5.77` | comma `1,234` | `$5.77` | `en` |
| `pt` | comma `5,77` | dot `1.234` | `R$ 5,77` | `pt-BR` |
| `es` | comma `5,77` | dot `1.234` | `MX$ 5,77` (or original currency: `5,77 €` / `R$ 5,77`) | `es-MX` |

Dates: DE uses `DD.MM.YYYY`; EN uses `YYYY-MM-DD` or `Month D, YYYY`; PT uses `DD/MM/YYYY`; ES (es-MX) uses `DD/MM/YYYY` (or `D de Mes de YYYY` in prose, e.g. `16 de mayo de 2026`). Weekday names translate (Freitag → Friday → sexta-feira → viernes).

The chip-tag label inside `<span class="chip [hot|good]">…</span>` translates too: `Achtung` → `Heads up` / `Atenção` / `Atención`; `Wirtschaft` → `Economy` / `Economia` / `Economía`; etc. Keep the tag short (~1–2 words) and ALL CAPS if the source was ALL CAPS.

## File paths
- HTML output: `public/<category>/<lang>/{{YYYY-MM-DD}}.html` (relative to the project root — everything served lives under `public/`).
- `<category>` ∈ `economy`, `software`, `ai-dev`, `ai-usecases`, `family`, `jobs`, `learn-language`.
- `<lang>` ∈ `de`, `en`, `pt`, `es`.

A successful run emits **four files** per category per day (one per language). Each file is a complete standalone HTML document with the same body structure — only the visible text differs. No markdown twin.

The dashboard tracks which languages have a file for each date in its manifest (`entries[*].langs`). If a non-DE translation is missing for a given date, the dashboard transparently falls back to the DE file, so a partial run is non-fatal — but the goal is always all 4.

## HTML scaffold (REQUIRED) — scaffold + shared lib + component library

The daily newsletter HTML is **content-only**. All shared CSS and interactive JS live in `lib/`:

- **`lib/styles.css`** — all CSS (scaffold + atomic helpers + every component's styles + per-category accent overrides).
- **`lib/newsletter.js`** — auto-init for interactive components (R$/h calculator, FX pair/range switcher, sparklines, benchmark bar chart, Mermaid). Detects targets via classes + `data-component` attributes; no-op if a component isn't on the page.

The reference files:

- **`docs/template.html`** — the minimal skeleton each daily file starts from (~70 lines). Contains the masthead, dashboard wrapper, body-grid placeholders, and the `<link>` + `<script>` tags that pull in the shared lib. No inline styles, no embedded scripts.
- **`docs/COMPONENTS.md`** — fragment library. Each component shows only **HTML structure with data attributes**; its CSS and JS already live in `lib/`. CDN dependencies (Chart.js, Mermaid) are listed per component.

### How to build a daily newsletter
1. **Build the DE version first.** Copy `docs/template.html` as `public/economy/de/{{YYYY-MM-DD}}.html` (etc.). All research, ELI5 phrasing, story selection happens here. DE is canonical.
2. **Set the body class** to the right category: `<body class="cat-economy">`. That alone picks the accent colour — no inline `<style>` required.
3. **Set `<html lang>`** to match the language: `de` for the DE file, `en` / `pt-BR` / `es-MX` for the others.
4. **Fill the masthead** with day's headline, weekday + date, location, one-liner.
5. **Fill the TL;DR band** (top of `<main>`) with 6–12 bullets.
6. **Fill the timeline band** with the appropriate variant (7-day or multistage).
7. **For software / ai-dev / ai-usecases**: there's no per-category dashboard or "Top-Stories" tier — the timeline band goes directly into the body-grid. The day's headline stories are covered as full sections inside the body-grid columns. **For other categories**: fill the per-category `.dashboard` with the right components from `docs/COMPONENTS.md`.
8. **Fill the body-grid columns** with deep-dive sections per prompt (no TL;DR here — it's the top band).
9. **For interactive components** (FX panel, calculator, benchmark chart, Mermaid diagram):
   - Uncomment the matching CDN `<script>` line in `<head>`.
   - Add the required JSON data block at the end of `<body>`. Translate the labels inside the JSON (e.g. `"label": "EUR/BRL"`) but keep numeric data and IDs identical across languages.
10. **Lib path:** the include tags in `docs/template.html` are `../../lib/styles.css` and `../../lib/newsletter.js` — two levels up, because the daily file lives at `<category>/<lang>/<date>.html`. Don't shorten.
11. **Self-check before save (DE file):** file includes `masthead-title`, `tldr`, `timeline`, and `body-grid`. Complete standalone HTML document (`<!DOCTYPE html>` … `</html>`) because `index.html` iframe-embeds it. **No `<style>` or `<script>` blocks inside `<body>` (the only allowed `<script>` tags are the CDN imports + lib include in `<head>`, and inline `<script type="application/json">` data blocks at end of `<body>`).**
    - **Länge zuerst, dann übersetzen:** Trimme die DE-Datei auf das Wortlimit des Newsletters (Standard 1500–2500 Wörter, sofern der Task-Prompt nichts anderes sagt) **bevor** Schritt 12 läuft — Übersetzungen blähen sich um 15–30 % auf (PT/ES werden am längsten), also kürzt Trimmen am DE-Original alle vier Sprachen auf einmal. Keine Cross-Spalten-Dopplung: eine Story = eine Sektion.
    - **Headline-Disziplin:** die `<h1 class="masthead-title">` ist **eine Zeile, ein Gedanke** (~max. 12 Wörter / ~70 Zeichen, kein zweiter Satz, kein „A, B und jetzt C"). Mehrere Aufhänger gehören in den TL;DR-Lead, nicht in die Schlagzeile.
    - **Keine Gerüst-Kommentare im Output:** die Scaffold-/Autor-Kommentare aus `docs/template.html` (`<!-- BAND 2: … -->` etc.) aus der finalen Datei löschen — sie sind Rauschen und lecken sonst (oft auf Deutsch) in die Übersetzungen.
12. **Translate to EN, PT, ES.** Copy the DE file three times (one per language target folder), keep the entire HTML structure identical, then translate the visible text in place. Update:
    - `<html lang>` to the locale tag.
    - `<title>` text.
    - All narrative prose, headings, callouts, chip labels, button text, alt text, aria-label.
    - Numeric separators per the per-locale table above.
    - Date strings in the masthead-issue line and inline (DE: `2026-05-16`, EN: `2026-05-16`, PT: `16/05/2026`, ES: `16/05/2026`).
    - Weekday names in the timeline rows.
    - Translate JSON data-block labels (the `"label"` keys), but **do not** touch numeric values, IDs, or canonical-form proper nouns.
    - **HTML comments:** there should be no scaffold comments in the output (see step 11); if any remain, they must **not** be German in the EN/PT/ES files — translate or delete them.
    Source URLs remain the originals; if a story has an authoritative non-DE source (PT-BR for Brazilian stories, etc.), prefer that source language for the link target rather than translating the URL.

### Which components fit which newsletter
| Newsletter | Typical components |
|---|---|
| economy | `fx-card-set` · `fx-detail-panel` · `r-hour-calculator` · `event-timeline-multistage` · `scenario-block` · optionally `causal-chain-mermaid` |
| software | `event-timeline-7day` |
| ai-dev | `event-timeline-7day` · `benchmark-bar-chart` (when a benchmark moves) |
| ai-usecases | `event-timeline-7day` · `projekt-ideen-twiced` (closing) |
| family | `weather-card` · `wochenend-pick-card` · `activity-table` · `event-timeline-7day` |
| jobs | `jobs-board` (full-width paginated listings, sorted by fit) · `event-timeline-7day` |
| learn-language | `vocab-list` (full-width four-cell rows + `<details>` conjugation drawer; `.speak` voice buttons per word) |

The list above is a guide, not a contract. If a different mix makes a particular day's content clearer, use it.

## Atomic helpers (built into `docs/template.html`)

These CSS classes are pre-defined in the template scaffold. Use them inside body sections to keep formatting consistent across newsletters.

| Class | Purpose | Example |
|---|---|---|
| `.news-item` | Headline + body + source-link entry | `<article class="news-item"><h3>…</h3><p>…</p><span class="src"><a href="…">domain</a></span></article>` |
| `.callout` (+ `.warn` / `.info`) | Boxed aside with optional label | `<div class="callout warn"><span class="callout-label">Achtung</span> …</div>` |
| `.eli5` (+ `.eli5-term`) | First-time term explainer (ELI5 rule) | `<div class="eli5"><strong class="eli5-term">OIS-Spread:</strong> Banken wetten…</div>` |
| `.mechanism` (+ `.step` / `.arrow`) | Inline causal chain | `<div class="mechanism"><span class="step">A</span><span class="arrow">→</span><span class="step">B</span></div>` |
| `.pro-con` (+ `.pro` / `.con`) | Two-column comparison | See `docs/template.html` CSS comments for full pattern. |
| `.update-since` | Inline "since Monday" diff marker | `<span class="update-since">Update seit Mo</span> IPCA über Erwartung…` |
| `.stat` | Inline numeric highlight | `Selic bei <span class="stat">13,75 %</span>.` |
| `.h2-refs` | Footnote refs that apply to the whole section, placed inside the `<h2>` | `<h2>Netlogon CVE-2026-41089 <span class="h2-refs">[7][8][9]</span></h2>` |

### Source-link convention (unified across newsletters)

There is **one** convention for sourcing, used by every newsletter:

1. **Per-claim refs in prose.** Inline `<sup>[N]</sup>` (or `[N]` styled as a footnote ref) next to the specific sentence the source supports — typically inside a paragraph after the strongest claim.
2. **Section-wide refs on the `<h2>`.** When *all* sources for a section apply to the whole paragraph (not to one specific claim), append a single `<span class="h2-refs">[7][8][9]</span>` inside the `<h2>` after the title text. Do **not** also write a separate `Quellen: [7] · [8] · [9]` line — the title-level refs make it redundant.
3. **Footnote glossary.** Each section ends with a `<div class="footnotes"><ol>…</ol></div>` (or the `.src` block) that resolves the numbers to actual URLs. The user clicks `[7]` (whether on the title or in prose) to jump down to source 7.

Pick (1) or (2) per section — never both. (1) is the default when one paragraph has multiple unrelated sources; (2) is the right choice when one news-item is essentially "summary of these N sources together." The earlier *trailing* `Quellen: [7] · [8] · [9]` paragraph is removed across all newsletters; use the title-level pill instead.

These are **CSS-only utilities** — atomic, generic, no domain bias. Components in `docs/COMPONENTS.md` are bigger structured fragments with HTML + CSS + JS together.

## Theme color (REQUIRED per category)
Set via `<body class="cat-{category}">`. The accent colours are baked into `lib/styles.css`:

| Category          | `--accent` light | `--accent` dark |
|-------------------|------------------|------------------|
| `economy`         | `#b9462a` | `#e08260` |
| `software`        | `#3a6ea5` | `#6fa1d8` |
| `ai-dev`          | `#6a4ea0` | `#9d83cf` |
| `ai-usecases`     | `#2d8a87` | `#6ec0bc` |
| `family`          | `#c08735` | `#e0a85a` |
| `jobs`            | `#4a6680` | `#87a6c4` |
| `learn-language`  | `#9c3858` | `#d18299` |

Do not put `<style>` blocks in daily HTML files. To change a category accent, edit `lib/styles.css`.

## Chart.js gotcha — positioned wrappers
All canvases must sit inside a wrapper with explicit height. Otherwise Chart.js + `maintainAspectRatio: false` inside a flex parent triggers an infinite resize loop. The Chart.js-using components in `docs/COMPONENTS.md` (e.g. `fx-card-set`, `fx-detail-panel`, `benchmark-bar-chart`) already include the correct wrapper CSS — paste them as-is, don't restructure their markup.

## Standard sections per newsletter

The page reads top-to-bottom as an inverted pyramid: scan tools first, then per-category context, then deep dives. The first three bands are the same for every newsletter — only the dashboard and body-grid contents vary.

1. **Masthead** — date, weekday, location, one-line headline.
2. **TL;DR band** (full width, sibling of `.body-grid` — NOT inside the body-grid). Opens with an optional `<p class="lead">` editorial frame (drop cap in accent), followed by 6–12 bullets, each starting with `<span class="chip [hot|good]">TAG</span>`. No box chrome — the whole section IS the executive summary, with weight from typography alone. Bullets render in two scan-columns on wide viewports. The voice-reader 🔊 button on the `<h2>` reads the lead and all bullets in order.
3. **Wochenausblick / Event-Horizont band** (full width). `event-timeline-7day` for software/ai-dev/ai-usecases/family/jobs; `event-timeline-multistage` for economy. The "what do I need to plan around?" scan.
4. **Per-category dashboard** (optional — only for categories with specialised cards):
   - **economy** → `.dashboard` (FX-card-set + fx-detail-panel) + `.strip` (R$/h calculator).
   - **family** → `.dashboard` (weather-card + wochenend-pick-card).
   - **jobs** → no `.dashboard`; a full-width `jobs-board` (direct child of `.shell`, like the timeline) holds all listings with pagination, sorted by fit score.
   - **software / ai-dev / ai-usecases** → no dashboard. The timeline band goes straight into the body-grid. The day's headline stories are written as full sections inside the body-grid — there's no intermediate "Top-Stories" tier.
5. **Body-grid** — deep-dive sections. 3 columns for content-dense newsletters (economy, software, ai-dev, ai-usecases); `body-grid.cols-2` (2 columns) for tighter ones (family, jobs). **TL;DR is no longer inside the body-grid** — it's the top band.

## Rules
- Every non-trivial claim gets a source link.
- Skip a section if there's nothing material to say. Don't pad.
- Skip recaps of items older than 48h unless there's a fresh update.
- Cite sources inline as `<a href="...">Domain</a>` or `<a href="...">Outlet</a>`.
- Research in DE/PT-BR/EN/ES as needed. Draft in **German first** (canonical), then translate the finished DE file into EN, PT, ES — do not re-research per language.

## Voice-summary block (REQUIRED on every newsletter)

The top-right 🔊 megaphone reads a **separate, hand-written voice summary** — not the visible page text. Walking the page line-by-line produces a stuttering "Headline. Subhead. Bullet. Source." that doesn't sound like a story. Instead, every newsletter authors a hidden `<div class="voice-summary" hidden>` block right before `</body>`:

```html
<div class="voice-summary" hidden aria-hidden="true">
  <p>Intro paragraph — opens with weekday/date in prose: „Es ist Samstag, der 16. Mai. Drei Tage vor Google I/O ist der News-Tag selbst leise…"</p>
  <p>One paragraph per story, written as narration. No „Punkt eins"/„Punkt zwei", no chip tags read aloud, no bracket numbers like „[7]". Refer to sources naturally: „laut Reuters", „wie Bloomberg berichtet".</p>
  <p>Numbers spelled in a way that reads well aloud: „fünf Komma acht acht" für 5,88; „drei Tausend" für 3000.</p>
  <p>Closing sentence — what to watch for next.</p>
</div>
```

Rules:
- **Hidden from view** via the `hidden` attribute (the voice-reader still walks the DOM and picks it up; sighted users read the visible page).
- **5–10 paragraphs**, each ~2–4 sentences. Roughly 4–7 minutes of speech.
- **Narration voice**, not bullet voice. No „Erstens / Zweitens", no semicolon-stacked clauses. Short declarative sentences.
- **No HTML chrome**: no `<h2>`, no chip spans, no `[N]` footnote refs, no inline `<code>`. The voice reader walks only `<p>` and `<li>` inside `.voice-summary`.
- **Translated per language**: every per-language file gets its own voice-summary written in that language's idiom, not a machine-translation of the DE version. EN reads American-press style, PT-BR reads Brazilian-press style, ES (es-MX) reads neutral Mexican Spanish.
- **Closing**: include a one-sentence wrap that says what tomorrow's brief will likely cover, so the listener knows the segment is ending.

The per-section 🔊 buttons (`.read-btn` next to each `<h2>`) still read the *visible* section text — that's the deep-dive mode. Only the top-right "read whole newsletter" button uses the voice-summary block.

## Delivery
No email delivery. The agent writes **four HTML files** per category per day, one per language, into `<category>/<lang>/{{YYYY-MM-DD}}.html`. The dashboard task (`morning-brief-dashboard`, scheduled separately at 06:30 local) scans these files and rebuilds the `window.__MANIFESTS` block in `index.html`. Do not edit `index.html` from a newsletter task.
