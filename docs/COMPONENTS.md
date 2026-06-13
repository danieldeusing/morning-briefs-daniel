# Morning Brief — Component Library

Reusable HTML fragments. Daily newsletters are content-only: they include `lib/styles.css` (which carries all component CSS) and `lib/newsletter.js` (auto-init for interactive components). This file documents the **HTML pattern** for each component plus, where needed, the data-attribute / JSON contract that the JS expects.

## How to assemble a newsletter

1. **Copy `docs/template.html` as the daily file** at `<category>/{{YYYY-MM-DD}}.html`.
2. **Set the body class** to `cat-<category>` (e.g. `<body class="cat-economy">`). That alone picks the accent colour — no inline `<style>` needed.
3. **Pick components below** matching your prompt's Dashboard + body specs. Paste each component's HTML into the matching slot.
4. **For interactive components** (FX panel, calculator, benchmark chart, Mermaid diagram):
   - Add the **CDN `<script>` tag** to `<head>` (uncomment the relevant line in the template).
   - Include the required JSON data block at the end of `<body>` (see component below).
   - `lib/newsletter.js` auto-detects the component and wires it up. Don't add inline `<script>` blocks.
5. **Fill the masthead** with day's headline, weekday + date, location, one-liner.
6. **Self-check before save:** file should contain `masthead-title`, `dashboard`, `body-grid`. Open in a browser — verify nothing is broken.

**No inline `<style>` or `<script>` in daily files.** Everything shared lives in `/lib/`.

---

## Components index

> **Read only what you need.** This library is long. Read this index + the
> "How to assemble" section above, then read ONLY the specific `` ## `<component>` ``
> sections your category actually uses (the "Used by" column tells you which —
> grep the header and read that block). Do not read the whole file end to end.

| Component | Used by | Interactive? |
|---|---|---|
| [`fx-card-set`](#fx-card-set) | economy | sparkline charts |
| [`fx-detail-panel`](#fx-detail-panel) | economy | switchable chart |
| [`r-hour-calculator`](#r-hour-calculator) | economy | live slider |
| [`scenario-block`](#scenario-block) | economy | — |
| [`benchmark-bar-chart`](#benchmark-bar-chart) | ai-dev | bar chart |
| [`projekt-ideen-twiced`](#projekt-ideen-twiced) | ai-usecases | — |
| [`freiburg-match-card`](#freiburg-match-card) | football | — |
| [`standings-mini-table`](#standings-mini-table) | football (optional teaser) | — |
| [`standings-full-table`](#standings-full-table) | football (**mandatory** Bundesliga + Brasileirão) | — |
| [`form-curve`](#form-curve) | football | — |
| [`weather-card`](#weather-card) | family | — |
| [`wochenend-pick-card`](#wochenend-pick-card) | family | — |
| [`activity-table`](#activity-table) | family | — |
| [`jobs-board`](#jobs-board) | jobs | full-width paginated listings, sorted by fit |
| [`event-timeline-7day`](#event-timeline-7day) | shared | — |
| [`event-timeline-multistage`](#event-timeline-multistage) | economy | — |
| [`causal-chain-mermaid`](#causal-chain-mermaid) | economy, ai-dev, ai-usecases | rendered diagram |

---

## `fx-card-set`

Used by: economy · CDN: **Chart.js** · Slot: `.dashboard` (left)

```html
<div class="fx-cards">
  <article class="fx-card primary">
    <div class="fx-pair">EUR / BRL · ECB</div>
    <div class="fx-rate">{{EUR_BRL}}</div>
    <div class="fx-delta up">▲ {{±X.XX}} %</div>
    <div class="fx-spark-wrap"><canvas id="spark-eurbrl"></canvas></div>
    <div class="fx-note">{{1-Zeiler-Kontext}} · <a href="https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-brl.en.html">ecb.europa.eu</a></div>
    <div class="fx-time">Stand: {{DD.MM.YYYY HH:MM}} BRT</div>
  </article>
  <article class="fx-card">
    <div class="fx-pair">USD / BRL</div>
    <div class="fx-rate">{{USD_BRL}}</div>
    <div class="fx-delta down">▼ {{±X.XX}} %</div>
    <div class="fx-spark-wrap"><canvas id="spark-usdbrl"></canvas></div>
    <div class="fx-note">{{Kontext}} · <a href="https://tradingeconomics.com/brazil/currency">tradingeconomics.com</a></div>
    <div class="fx-time">Stand: {{DD.MM.YYYY HH:MM}} BRT</div>
  </article>
  <article class="fx-card">
    <div class="fx-pair">DXY · USD gegen Weltkorb</div>
    <div class="fx-rate">{{DXY}}</div>
    <div class="fx-delta up">▲ {{±X.XX}} %</div>
    <div class="fx-spark-wrap"><canvas id="spark-dxy"></canvas></div>
    <div class="fx-note">{{Kontext}} · <a href="https://www.fxstreet.com/rates-charts/dollar-index">fxstreet.com</a></div>
    <div class="fx-time">Stand: {{DD.MM.YYYY HH:MM}} BRT</div>
  </article>
</div>
```

**Rules:**
- `.fx-pair` is a **single-line label** — pair name + short source tag (`EUR / BRL · ECB`, not `EUR / BRL · KREUZKURS ECB-KONSISTENT`). Long context belongs in `.fx-note`. Overflowing text is auto-ellipsised, so visually you'll lose information silently — keep it short.
- **Do NOT use Wise as a source.** The public Wise widget (`wise.com/.../eur-to-brl-rate`) caches aggressively and showed multi-day stale rates in May 2026 (widget claimed 6,04 while in-app rate was 5,87). Stick to ECB Reference for the primary EUR/BRL value; cross-check with exchange-rates.org or the USD/BRL × EUR/USD cross from TradingEconomics.
- `.fx-note` carries the one-line context + the source link.
- `.fx-time` is **mandatory** — every card must show when the rate was sampled, format `DD.MM.YYYY HH:MM BRT` (Brasília time, since Daniel reads in Ribeirão Claro). Pulls from `§ 0 Recherche-Disziplin` of `docs/CROSS_CUTTING.md` — every number gets a timestamp.

Sparklines are driven by the same `#fx-series` JSON used by `fx-detail-panel` — see below.

---

## `fx-detail-panel`

Used by: economy · CDN: **Chart.js** · Slot: `.dashboard` (right)

```html
<div class="detail-panel" data-component="fx-detail-panel">
  <div class="detail-head">
    <div>
      <div class="detail-title">Verlauf · <span id="detail-pair-label">EUR/BRL</span></div>
      <div class="detail-sub" id="detail-sub">Letzte Woche (täglich).</div>
    </div>
    <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">
      <div class="range-toggle" id="pair-toggle">
        <button data-pair="eurbrl" class="active" type="button">EUR/BRL</button>
        <button data-pair="usdbrl" type="button">USD/BRL</button>
        <button data-pair="dxy" type="button">DXY</button>
      </div>
      <div class="range-toggle" id="range-toggle">
        <button data-range="W" class="active" type="button">Woche</button>
        <button data-range="M" type="button">Monat</button>
        <button data-range="Y" type="button">Jahr</button>
      </div>
    </div>
  </div>
  <div class="detail-chart-wrap"><canvas id="detail-chart"></canvas></div>
</div>
```

Put this JSON at end of `<body>`:

```html
<script type="application/json" id="fx-series">
{
  "eurbrl": { "label": "EUR/BRL",
              "W": {"labels": ["Mi","Do","Fr","Mo","Di"], "data": [5.85, 5.87, 5.91, 5.88, 5.92]},
              "M": {"labels": [...], "data": [...]},
              "Y": {"labels": [...], "data": [...]} },
  "usdbrl": { "label": "USD/BRL", "W": {...}, "M": {...}, "Y": {...} },
  "dxy":    { "label": "DXY",     "W": {...}, "M": {...}, "Y": {...} }
}
</script>
```

Colour per pair is auto-picked from `--warn` / `--accent` / `--accent-2`. To override, add `"color": "#hex"` to a pair object.

---

## `r-hour-calculator`

Used by: economy · CDN: none · Slot: `.strip` (left)

```html
<div class="calc" data-component="r-hour-calc"
     data-yday="5.85" data-base="6.00" data-eur-per-hour="100">
  <div class="calc-header">
    <div>
      <div class="calc-title">R$/h-Rechner</div>
      <div class="calc-sub">Fix-Stundensatz — schieben für Szenarien.</div>
    </div>
    <div class="calc-out"><span id="calc-out">R$610</span>/h</div>
  </div>
  <div class="calc-row">
    <span class="calc-edge">5,50</span>
    <input type="range" min="5.50" max="6.30" step="0.01" value="5.92">
    <span class="calc-edge">6,30</span>
    <span class="calc-value">5,920</span>
  </div>
  <div class="calc-detail">
    <span>ggü. Vortag (5,85): <span class="calc-delta" id="calc-delta-yday">—</span></span>
    <span>ggü. Ø 2025 (6,00): <span class="calc-delta" id="calc-delta-base">—</span></span>
  </div>
</div>
```

`data-yday` = yesterday's rate · `data-base` = baseline (Ø 2025) · `data-eur-per-hour` = the hourly rate the calculator multiplies by (illustrative default 100).

---

## `scenario-block`

Used by: economy (12-month structural section) · CDN: none · Slot: body section

```html
<div class="scenarios">
  <div class="scenario base"><span class="scenario-prob">60 %</span><strong>Base:</strong> EUR/BRL {{X.XX}}–{{Y.YY}} bis Q4 weil {{Treiber}}.</div>
  <div class="scenario bear"><span class="scenario-prob">25 %</span><strong>Bear-für-BRL:</strong> > {{Z.ZZ}} weil {{Treiber}}.</div>
  <div class="scenario bull"><span class="scenario-prob">15 %</span><strong>Bull-für-BRL:</strong> < {{W.WW}} weil {{Treiber}}.</div>
</div>
```

---

## `benchmark-bar-chart`

Used by: ai-dev (when a benchmark moves) · CDN: **Chart.js** · Slot: body section

```html
<div class="bench-wrap" data-component="benchmark-chart">
  <div class="bench-head">SWE-Bench Verified — Top 6, Stand {{date}}</div>
  <div class="bench-chart-wrap"><canvas></canvas></div>
</div>
```

Put this JSON at end of `<body>`:

```html
<script type="application/json" id="bench-data">
{"labels": ["Claude Sonnet 4.6","GPT-5","Gemini Code 2.5","DeepSeek-Coder V3","Qwen-Coder 3","Codestral 2"],
 "data":   [69.5, 64.8, 61.0, 58.2, 56.7, 52.3],
 "max":    80,
 "unit":   " %"}
</script>
```

---

## `projekt-ideen-twiced`

Used by: ai-usecases (closing section) · CDN: none · Slot: body section, last

```html
<section class="twiced-ideen">
  <h2>Projekt-Ideen für twiceD</h2>
  <p class="byline">Kuratierte B2B-Opportunitäten aus heutigen News + 7d-Kontext</p>
  <div class="idee">
    <strong>Muster:</strong> {{"Mid-market DE-X kauft Y für Z."}}<br>
    <strong>twiceD-Fit:</strong> {{Stack-Match, realistische Team-Größe}}<br>
    <strong>Lead-Hinweis:</strong> {{Branche / Plattform / Hook}}
  </div>
  <!-- 1–3 more .idee -->
</section>
```

---

## `freiburg-match-card`

Used by: football · CDN: none · Slot: `.dashboard` (left, top card)

```html
<article class="match-card freiburg">
  <div class="match-head">
    <span class="match-club">SC Freiburg</span>
    <span class="match-comp">{{Bundesliga}}</span>
  </div>
  <div class="match-result">
    <span class="match-label">Letztes Spiel</span>
    <strong>{{SCF 2:1 Gegner}}</strong> · {{datum}}
  </div>
  <div class="match-next">
    <span class="match-label">Nächstes Spiel</span>
    <strong>{{Gegner}}</strong> · {{datum}} · {{H/A}}
  </div>
</article>
```

---

## `standings-mini-table`

Used by: football (compact top-N teaser, optional) · CDN: none · Slot: dashboard card

For at-a-glance dashboard summaries. Daniel has explicitly asked for full tables in the body — use [`standings-full-table`](#standings-full-table) below for the Bundesliga and Brasileirão sections. This mini variant is only for dashboard teasers if you want one.

```html
<article class="fx-card">
  <div class="fx-pair">{{Bundesliga}} · Top 3</div>
  <table class="mini-table">
    <thead><tr><th>#</th><th>Verein</th><th>Pkt</th><th>TD</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>{{Team1}}</td><td>{{P1}}</td><td>{{TD1}}</td></tr>
      <tr><td>2</td><td>{{Team2}}</td><td>{{P2}}</td><td>{{TD2}}</td></tr>
      <tr><td>3</td><td>{{Team3}}</td><td>{{P3}}</td><td>{{TD3}}</td></tr>
    </tbody>
  </table>
</article>
```

## `standings-full-table`

Used by: football (Bundesliga + Brasileirão Série A — **mandatory in every brief**) · CDN: none · Slot: body section

**Required every day.** Complete league standings — all 18 teams (Bundesliga) or 20 teams (Brasileirão Série A). Use `data-zone` on each `<tr>` to colour-code the rank cell:

- `ucl`  — Champions League / Libertadores group stage
- `el`   — Europa League / Libertadores qualifying
- `conf` — Conference League / Copa Sudamericana
- `play` — Relegation play-off
- `rel`  — Direct relegation

Add `class="highlight"` on SC Freiburg's row (Bundesliga) to make it stand out.

**Bundesliga zones (current convention):** rows 1–4 = `ucl`, row 5 = `el`, row 6 = `conf`, row 16 = `play`, rows 17–18 = `rel`.

**Brasileirão Série A zones (current convention):** rows 1–4 = `ucl` (Libertadores group), rows 5–6 = `el` (Libertadores pre), rows 7–12 = `conf` (Sudamericana), rows 17–20 = `rel`.

If zone conventions change (new UEFA/CBF rules), adapt the row tagging.

```html
<div class="standings-table-wrap">
  <h3>Bundesliga · Tabelle nach Spieltag {{N}} (Stand {{DD.MM.YYYY HH:MM}}, Quelle: kicker.de)</h3>
  <table class="standings-table">
    <thead>
      <tr><th>#</th><th>Verein</th><th>Sp</th><th>S</th><th>U</th><th>N</th><th>Tore</th><th>TD</th><th>Pkt</th></tr>
    </thead>
    <tbody>
      <tr data-zone="ucl"><td>1</td><td>{{Team}}</td><td>33</td><td>24</td><td>7</td><td>2</td><td>89:31</td><td>+58</td><td>79</td></tr>
      <tr data-zone="ucl"><td>2</td><td>{{Team}}</td><td>33</td><td>23</td><td>5</td><td>5</td><td>91:43</td><td>+48</td><td>74</td></tr>
      <tr data-zone="ucl"><td>3</td><td>{{Team}}</td><td>33</td><td>22</td><td>4</td><td>7</td><td>78:39</td><td>+39</td><td>70</td></tr>
      <tr data-zone="ucl"><td>4</td><td>{{Team}}</td><td>33</td><td>19</td><td>8</td><td>6</td><td>72:38</td><td>+34</td><td>65</td></tr>
      <tr data-zone="el"><td>5</td><td>{{Team}}</td><td>33</td><td>17</td><td>11</td><td>5</td><td>67:42</td><td>+25</td><td>62</td></tr>
      <tr data-zone="conf"><td>6</td><td>{{Team}}</td><td>33</td><td>14</td><td>11</td><td>8</td><td>54:42</td><td>+12</td><td>53</td></tr>
      <tr class="highlight"><td>7</td><td>SC Freiburg</td><td>33</td><td>13</td><td>9</td><td>11</td><td>43:48</td><td>−5</td><td>48</td></tr>
      <!-- continue through row 18 -->
      <tr data-zone="play"><td>16</td><td>{{Team}}</td><td>33</td><td>9</td><td>7</td><td>17</td><td>34:55</td><td>−21</td><td>34</td></tr>
      <tr data-zone="rel"><td>17</td><td>{{Team}}</td><td>33</td><td>4</td><td>6</td><td>23</td><td>36:76</td><td>−40</td><td>18</td></tr>
      <tr data-zone="rel"><td>18</td><td>{{Team}}</td><td>33</td><td>3</td><td>7</td><td>23</td><td>32:78</td><td>−46</td><td>16</td></tr>
    </tbody>
  </table>
  <div class="standings-legend">
    <span class="ucl">Champions League</span>
    <span class="el">Europa League</span>
    <span class="conf">Conference League</span>
    <span class="play">Relegations-Playoff</span>
    <span class="rel">Abstieg</span>
  </div>
</div>
```

For Brasileirão swap labels in the legend: `Libertadores`, `Libertadores Pré`, `Sudamericana`, (no play-off in BR Série A), `Rebaixamento`.

---

## `form-curve`

Used by: football (Freiburg's last 5) · CDN: none · Slot: body section

```html
<div class="form-curve">
  <div class="form-label">Form (letzte 5)</div>
  <div class="form-dots">
    <span class="dot win"  title="Sieg gg Augsburg 2:1">S</span>
    <span class="dot draw" title="Remis gg Mainz 1:1">U</span>
    <span class="dot loss" title="Niederlage gg BVB 0:2">N</span>
    <span class="dot win"  title="…">S</span>
    <span class="dot win"  title="…">S</span>
  </div>
</div>
```

---

## `weather-card`

Used by: family · CDN: none · Slot: `.dashboard` (left, top card)

```html
<article class="weather-card">
  <div class="weather-head">Wetter · Ribeirão Claro</div>
  <div class="weather-today">
    <div class="weather-temp">{{Tmax}}°/{{Tmin}}°</div>
    <div class="weather-cond">{{Bewölkt mit Schauern}}</div>
    <div class="weather-rain">Regen: {{XX %}}</div>
  </div>
  <div class="weather-forecast">
    <div class="wf-day"><span class="wf-date">Fr</span><span class="wf-temp">{{T}}°/{{T}}°</span></div>
    <div class="wf-day"><span class="wf-date">Sa</span><span class="wf-temp">{{T}}°/{{T}}°</span></div>
    <div class="wf-day"><span class="wf-date">So</span><span class="wf-temp">{{T}}°/{{T}}°</span></div>
  </div>
  <div class="weather-source"><a href="https://climatempo.com.br">climatempo.com.br</a></div>
</article>
```

---

## `wochenend-pick-card`

Used by: family · CDN: none · Slot: `.dashboard` (second card)

```html
<article class="weekend-pick">
  <div class="wp-head">Wochenend-Pick</div>
  <h3>{{Aktivität}}</h3>
  <div class="wp-meta">
    <span><strong>Wo:</strong> {{Ort}}</span>
    <span><strong>Wann:</strong> {{Tag, Uhrzeit}}</span>
    <span><strong>Alter:</strong> {{Eignung}}</span>
    <span><strong>Preis:</strong> R$ {{xx}}</span>
  </div>
  <p class="wp-note">{{Schatten? Wickelraum? Klima?}}</p>
  <a href="{{url}}">{{Quelle}}</a>
</article>
```

---

## `activity-table`

Used by: family · CDN: none · Slot: `.dashboard` (right detail) or body

```html
<div class="activity-panel">
  <h3>Aktivitäten der Woche</h3>
  <table class="activity-table">
    <thead><tr><th>Datum</th><th>Wo</th><th>Was</th><th>Alter</th><th>Preis</th><th>Quelle</th></tr></thead>
    <tbody>
      <tr><td>Sa 16.05</td><td>{{Ort}}</td><td>{{Was}}</td><td>{{1–8}}</td><td>R$ {{n}}</td><td><a href="{{url}}">{{D}}</a></td></tr>
      <!-- 4–6 more rows -->
    </tbody>
  </table>
</div>
```

---

## `jobs-board`

Used by: jobs · CDN: none · Slot: **full-width**, direct child of `<main class="shell">` (like the timeline band) — NOT inside `.dashboard`/`.body-grid`.

A single full-width, paginated listing board. **Data-driven**: the routine emits an *empty* `<section class="jobs-board">` plus an inline `<script type="application/json" id="jobs-listings">` payload (same pattern as `fx-series`). `lib/newsletter.js` (`initJobsBoard`) reads the payload, sorts by `fit_score` desc, builds the rows, paginates them (default 20/page), and injects the fit-% badge, tag chips, the collapsible scoring breakdown, a meta line, and a pager.

```html
<section class="jobs-board" data-component="jobs-board" data-page-size="20">
  <!-- intentionally empty — initJobsBoard() renders the rows from the JSON below -->
</section>

<script type="application/json" id="jobs-listings">
{
  "generated": "2026-05-20",
  "listings": [
    {
      "id": "fm-fpd-link-optimus",
      "title": "Yocto Linux Entwickler – FPD-Link",
      "company": "Optimus Search (end client: …)",
      "role_type": "freelance",
      "url": "https://www.freelancermap.de/projekt/…",
      "location": "100% remote",
      "salary_range": "110–130 €/h*",
      "date_posted": "n/a",
      "fit_score": 95,
      "fit_reason": "stack 43 + loc 20 + rate 12 + intrigue 5 + track 10 + pref 0 = 95",
      "tags": ["Embedded", "Yocto", "Remote"],
      "source": "freelancermap.de"
    }
    // …as many listings as researched (100+ fine); JS shows 20/page…
  ]
}
</script>
```

`*` = rate researched, not from the listing itself.

**Listing fields (per object in `listings[]`):**
- `id` **(required)** — unique key for the listing (slug of `source|company|title`, or a hash of the source URL).
- `title`, `company`, `location`, `salary_range`, `url`, `source` — rendered as-is.
- `fit_score` — integer 0–100; drives the fit-% badge and the default sort (desc).
- `role_type` — `freelance` (→ twiceD accent stripe) · `employee` (→ accent-2 stripe) · `intriguing` (→ muted stripe).
- `tags` — array of short strings, rendered as chips.
- `fit_reason` — the score breakdown, shown in a collapsible `<details>` under the listing.
- `date_posted` — shown if not `"n/a"`.

Top-level keys other than `listings` (`generated`, `profile_version`, `scoring`, `_comment`) are ignored by the renderer — keep them for provenance if useful. The renderer binds on `data-component="jobs-board"` (class-name agnostic), so the container class is `jobs-board`.

Keep the **Market-Pulse** blurb as a normal `.callout` or short `<p>` *above* the board, not inside the JSON.

---

## `event-timeline-7day`

Used by: software, ai-dev, ai-usecases, football, family, jobs · CDN: none · Slot: full-width band, directly below the TL;DR band (above the per-category dashboard, or — for software / ai-dev / ai-usecases — directly above the body-grid)

**Layout:** vertical day-list. Each `.tl-col` is one ROW (not a column), with date on left, dot on the vertical line in the middle, events on the right. Add as many days as needed — typical 7–9.

Markers per `.tl-col`:
- `class="tl-col today"` — green/accent dot for today.
- `class="tl-col hot"` — red/warn dot for a particularly significant day.
- Inside `.tl-events`, wrap individual items in `<span>`. The first `<span>` is bolded automatically (use it for the day's primary label).

```html
<div class="timeline">
  <div class="timeline-head">
    <div class="timeline-title">Wochenausblick</div>
    <div class="timeline-sub">{{Was bewegt — Kontext}}</div>
  </div>
  <div class="tl-track">
    <div class="tl-col today">
      <div class="tl-date">Do 14.05</div>
      <div class="tl-dot"></div>
      <div class="tl-events">
        <span>Heute</span>
        <span>{{Event A}}</span>
        <span>{{Event B}}</span>
      </div>
    </div>
    <div class="tl-col">
      <div class="tl-date">Fr 15.05</div>
      <div class="tl-dot"></div>
      <div class="tl-events">
        <span>{{Event}}</span>
      </div>
    </div>
    <!-- continue, one .tl-col per day -->
  </div>
</div>
```

---

## `event-timeline-multistage`

Used by: economy (6-stage horizon: Heute · Diese Woche · 30 Tage · 3 Monate · 6 Monate · 12 Monate) · CDN: none · Slot: full-width band, directly below the TL;DR band (replaces `event-timeline-7day` for economy)

Same component shell as `event-timeline-7day` — vertical list of rows. The `.tl-date` cell carries a label instead of a date, but the structure is identical:

```html
<div class="timeline">
  <div class="timeline-head">
    <div class="timeline-title">Event-Horizont</div>
    <div class="timeline-sub">Was kann EUR/BRL bewegen — gestaffelt</div>
  </div>
  <div class="tl-track">
    <div class="tl-col today">
      <div class="tl-date">Heute</div>
      <div class="tl-dot"></div>
      <div class="tl-events"><span>{{Event}}</span></div>
    </div>
    <div class="tl-col">
      <div class="tl-date">Diese Woche</div>
      <div class="tl-dot"></div>
      <div class="tl-events"><span>{{2–3 Events}}</span></div>
    </div>
    <div class="tl-col">
      <div class="tl-date">30 Tage</div>
      <div class="tl-dot"></div>
      <div class="tl-events"><span>{{Marquee-Events}}</span></div>
    </div>
    <div class="tl-col">
      <div class="tl-date">3 Monate</div>
      <div class="tl-dot"></div>
      <div class="tl-events"><span>{{Zyklus-Marker}}</span></div>
    </div>
    <div class="tl-col">
      <div class="tl-date">6 Monate</div>
      <div class="tl-dot"></div>
      <div class="tl-events"><span>{{Regime-Marker}}</span></div>
    </div>
    <div class="tl-col">
      <div class="tl-date">12 Monate</div>
      <div class="tl-dot"></div>
      <div class="tl-events"><span>{{Strukturell}}</span></div>
    </div>
  </div>
</div>
```

---

## `causal-chain-mermaid`

Used by: economy (kausale Pfade), ai-dev (Tool-Architektur), ai-usecases (Adoption-Pfade)
CDN: **Mermaid** · Slot: body section

```html
<pre class="mermaid">
graph LR
  A[EZB cut 25 bps] --> B[2y Bund-Treasury Spread −8 bps]
  B --> C[EUR/USD −0,4 %]
  C --> D[BRL flat vs USD]
  D --> E[EUR/BRL −0,3 %]
</pre>
```

Mermaid initialises automatically via `lib/newsletter.js` (if the Mermaid CDN script is loaded).

**Lighter alternative:** for single-line chains, use the atomic `.mechanism` helper (built into the template — no Mermaid CDN required):

```html
<div class="mechanism">
  <span class="step">EZB cut 25 bps</span><span class="arrow">→</span>
  <span class="step">2y Spread −8 bps</span><span class="arrow">→</span>
  <span class="step">EUR/USD −0,4 %</span>
</div>
```

---

## Notes

- **Daily newsletter HTML never contains inline `<style>` or `<script>` blocks.** Everything shared lives in `/lib/`.
- **CDN scripts** (Chart.js, Mermaid) are conditional: include them in `<head>` only when a component on the page needs them. Loading `lib/newsletter.js` is unconditional — it auto-detects what's on the page.
- **JSON data blocks** at end of `<body>` (e.g. `#fx-series`, `#bench-data`) are the only place numeric data lives; it stays inline rather than being a separate fetch.
- **Add new components** by extending this file AND adding the CSS to `lib/styles.css`. If interactive, extend `lib/newsletter.js` with an `initXxx()` function and call it from the `ready()` block.
