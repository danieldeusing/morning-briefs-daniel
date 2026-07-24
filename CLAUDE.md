# Morning Brief

Daily multi-newsletter generator. Ten category newsletters + one dashboard,
all served from a single static folder. Canonical language is German; every
brief is translated into EN, PT-BR, and es-MX.

## Layout

The repo root holds two kinds of content: what gets served at
`briefs.danieldeusing.de` (under `public/`) and the orchestration around it
(docs, data, tooling). Nothing outside `public/` is deployed.

```
morning-briefs/daniel/
├── CLAUDE.md                ← this file
├── public/                  ← deployed to Cloudflare Pages (everything served)
│   ├── index.html               dashboard (entry point; iframe-embeds the newsletters)
│   ├── favicon.svg
│   ├── lib/                     shared CSS, JS, fonts, brand-mark
│   ├── economy/                 per-category folders, each contains a per-language
│   │   ├── de/                      subfolder with YYYY-MM-DD.html files
│   │   ├── en/
│   │   ├── pt/
│   │   └── es/
│   ├── software/                (same de/en/pt/es structure)
│   ├── ai-dev/
│   ├── ai-usecases/
│   ├── family/
│   ├── jobs/
│   └── learn-language/
│
├── docs/                    ← editorial specs referenced by every routine
│   ├── FORMAT.md                shared layout/format spec
│   ├── COMPONENTS.md            fragment library
│   ├── CROSS_CUTTING.md         editorial principles (research, ELI5, voice)
│   └── template.html            canonical HTML scaffold (copied per daily file)
│
├── data/                    ← passive inputs (the jobs routine reads the CV from the
│   └── learn-language-ledger.json   public repo danieldeusing/cv-danieldeusing, not from here)
│
└── tools/
    └── build_manifest.py        rewrites window.__MANIFESTS in public/index.html
```

## Routines (one consolidated scheduled task)

All ten newsletters + the dashboard are produced by a **single** Claude Code
scheduled task (orchestrator), fired once daily at ~06:00 local:

```
~/.claude/scheduled-tasks/morning-briefs-daniel---morning-brief-all/SKILL.md
```

It replaced the former eleven per-category tasks (those still exist on disk but
are **disabled** — kept as backup/spec reference). All project tasks are
prefixed `morning-briefs-daniel---`. Inspect via the `scheduled-tasks` MCP
server (`mcp__scheduled-tasks__list_scheduled_tasks`) or the `/schedule` skill.

### How the orchestrator works

The orchestrator does no research itself — it dispatches **subagents per phase**,
keeping its own context lean (subagents write files to disk and return short
summaries). The point is **model right-sizing**: each phase runs on the cheapest
model that does its job well, set via the per-call `model:` parameter (full model
ids override the agent's frontmatter default).

| Phase | Subagent (`.claude/agents/`) | Model | Output |
|---|---|---|---|
| Research | `brief-researcher` | `claude-sonnet-4-6` | `/tmp/brief-research-<cat>-<date>.md` dossier (sourced facts) |
| Write **DE** | `brief-writer` | `claude-opus-4-8` (complex: economy, jobs) / `claude-opus-4-7` (medium: rest) | `public/<cat>/de/<date>.html` + `/tmp/brief-sources-<cat>-<date>.md` |
| Translate **EN/PT/ES** | `brief-translator` | `claude-sonnet-4-6` | `public/<cat>/{en,pt,es}/<date>.html` |
| Verify | `brief-fact-checker` | `claude-sonnet-4-6` | structured report → fix loop (cap 2 rounds) |
| Pre-research (jobs only) | `jobs-aggregator` | `claude-sonnet-4-6` | listings JSON (orchestrator calls it; subagents can't nest) |
| Dashboard | `tools/build_manifest.py --verify` | — | rewrites `window.__MANIFESTS` in `index.html` |
| Publish (last) | `git push` + `tools/deploy-cloudflare.sh` | — | pushes repo + deploys `public/` to Cloudflare Pages → briefs.danieldeusing.de |

The **coordinator** (the routine itself) wants Opus 4.8, but a desktop scheduled
task can't pin its own model — it inherits the app's default model at fire time,
so keep the app default on **Opus 4.8** for this routine.

Categories (canonical order): `economy, software, ai-dev,
ai-usecases, family, jobs, language`. Processed in
**batches of 3** (bounded concurrency — more triggers rate limits). Research is
split to a cheap model so the expensive Opus writers only reason over a sourced
dossier rather than doing the fetch-heavy legwork themselves.

### Where the per-category editorial spec lives

Each category's spec (reader profile, scope, content structure, sources) is a
version-controlled file the `brief-researcher` and `brief-writer` read:

```
docs/categories/<category>.md
```

**To change what a category covers, edit `docs/categories/<category>.md`** (in
this repo). To change the *flow* (phases, models, batching, fact-check gate),
edit the orchestrator SKILL.md. The disabled per-category SKILL.md files under
`~/.claude/scheduled-tasks/` are no longer authoritative.

The dashboard step runs last (folded into the orchestrator) and rewrites
`window.__MANIFESTS` in `public/index.html`; newsletters load via `<iframe>`.

## Theme tokens per category

Each category has a fixed accent color (override `--accent` in the newsletter's
inline CSS). See `docs/FORMAT.md` for the palette.

## How the HTML pages are wired

Two surfaces, sharing one design system.

```
┌───────────────────────────────────────────────────────────────┐
│ public/index.html ── dashboard chrome (sidebar + iframe host) │
│   <link rel="stylesheet" href="lib/tokens.css">                │
│   <iframe src="economy/de/2026-05-15.html">                    │
│              │                                                 │
│              ▼                                                 │
│   ┌─────────────────────────────────────────────────────────┐ │
│   │ <body class="cat-economy">                              │ │
│   │   <link rel="stylesheet" href="../../lib/styles.css">   │ │
│   │   <script defer src="../../lib/newsletter.js">          │ │
│   │   <header class="masthead"> … </header>                 │ │
│   │   <main class="shell">                                  │ │
│   │     <section class="tldr"> … </section>                 │ │
│   │     <div class="timeline"> … </div>                     │ │
│   │     <section class="dashboard"> … </section>  (optional)│ │
│   │     <div class="body-grid"> col col col </div>          │ │
│   │   </main>                                               │ │
│   └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Shared library — `lib/`

Three files own the entire visual system. Per-day HTML files never carry
inline `<style>` or `<script>` blocks (only `<script type="application/json">`
data is allowed at the end of `<body>`).

- **`lib/tokens.css`** — design tokens only. Surfaces (`--bg`, `--panel`),
  text (`--fg`, `--muted`, `--soft`), rules (`--rule`, `--rule-soft`),
  effects (`--shadow`), typography (`--headline-font`), semantic accents
  (`--warn`, `--good`), and the seven per-category accents (`--c-economy`,
  `--c-software`, `--c-ai-dev`, `--c-ai-usecases`, `--c-family`, `--c-jobs`,
  `--c-learn-language`). The active accent is `--accent`, aliased per
  newsletter via `body.cat-X { --accent: var(--c-X); }`. Full dark-mode
  block via `@media (prefers-color-scheme: dark)`. Loaded by both
  `index.html` (`<link>`) and `lib/styles.css` (`@import`).
- **`lib/styles.css`** — everything else: base typography, the masthead,
  full-width bands (TL;DR, timeline), `.dashboard` +
  `.strip` two-column grids, the 2/3-column `.body-grid`, atomic helpers
  (`.news-item`, `.callout`, `.eli5`, `.mechanism`, `.pro-con`,
  `.update-since`, `.stat`, `.chip`), every component's styles, the
  voice-reader UI, print rules, and responsive breakpoints (1280 / 1100 /
  900 / 720 / 600 / 380 px).
- **`lib/newsletter.js`** — auto-init for interactive components. Detects
  targets by class + `data-component` attributes and is a no-op when a
  component isn't on the page: FX pair/range switcher, R$/h calculator,
  sparklines, benchmark bar chart, Mermaid diagrams, voice-reader (Web
  Speech API, with floating panel + per-h2 🔊 buttons).

### Daily file scaffold

Every newsletter starts as a copy of `docs/template.html` (~70 lines, no
content). The agent sets the body class, fills the masthead, the TL;DR
band, the timeline band, the per-category dashboard (optional —
economy/family/jobs only), and the body-grid columns. CDN
scripts (Chart.js, Mermaid) are uncommented only when a component needs
them.

A daily file looks like:

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Morning Brief — {{Kategorie}} · {{YYYY-MM-DD}}</title>
  <base target="_blank">           <!-- escape the iframe on link click -->
  <link rel="stylesheet" href="../../lib/styles.css">
  <!-- optional CDN scripts, only if a component on this page needs them -->
  <script defer src="../../lib/newsletter.js"></script>
</head>
<body class="cat-economy">         <!-- one of cat-economy|software|ai-dev|… -->
  <header class="masthead"> … </header>
  <main class="shell">
    <section class="tldr"> … </section>
    <div class="timeline"> … </div>
    <!-- optional, only for categories with specialised dashboard cards: -->
    <section class="dashboard"> … </section>          <!-- economy/family/jobs -->
    <div class="body-grid">
      <div class="col"> … </div>
      <div class="col"> … </div>
      <div class="col"> … </div>
    </div>
  </main>
  <!-- optional inline JSON data blocks for interactive components -->
</body>
</html>
```

### Page anatomy (top → bottom = inverted pyramid)

1. **Masthead** — issue line (kicker), headline `<h1>`, date + location.
   Double-rule bottom border evokes a printed broadsheet. The
   "read whole newsletter" voice-reader button is injected by JS into
   the top-right.
2. **TL;DR band** — full-width summary section, no box chrome. Opens with
   an optional editorial lead paragraph (drop cap in accent), then a
   two-column bullet scan with chips. The 30-second elevator-pitch of the
   whole brief; the voice-reader hooks onto its `<h2>`.
3. **Event-Horizont / Wochenausblick** — full-width timeline (7-day for
   most categories, multi-stage for economy). Vertical dot column with a
   single rule, dates left-aligned, events right.
4. **Per-category dashboard** (optional) —
   • `.dashboard` (economy / family / jobs): two-column slot
     for the category's specialised cards (FX, match, weather, listings).
   • software / ai-dev / ai-usecases: no dashboard. The timeline band
     flows directly into the body-grid; headline stories are written as
     full sections inside the body-grid rather than as a separate "Top-
     Stories" tier.
5. **Body-grid** — 3-column (content-dense) or `.cols-2` (tighter
   categories) deep-dive sections. Drops to 2 col under 1280 px, 1 col
   under 720 px.

### Per-category accent system

`<body class="cat-economy">` is the single switch. `tokens.css` aliases
`--accent` to the matching `--c-X` token. Every accent-bearing element
(h2 left bar, TL;DR border, links, chips, callouts, fx-card borders,
weekend-pick stripe, voice-reader button) reads `var(--accent)`, so
changing the category's colour is a one-line edit in `tokens.css`.

### Atomic helpers vs. components

- **Atomic helpers** (CSS-only, generic): `.news-item`, `.callout`
  (+ `.warn` / `.info`), `.eli5` (+ `.eli5-term`), `.mechanism`
  (+ `.step` / `.arrow`), `.pro-con` (+ `.pro` / `.con`),
  `.update-since`, `.stat`, `.chip` (+ `.hot` / `.good`),
  `.lead::first-letter` drop cap, `.byline`, `.src` / `.src-date`.
- **Components** (HTML + CSS + optional JS): fragments pasted from
  `docs/COMPONENTS.md`. Each component's markup carries its required
  classes and data attributes; CSS + JS already live in `lib/`.

### Dashboard ↔ newsletter contract

The dashboard (`index.html`) discovers newsletters from the inlined
`window.__MANIFESTS` object, rebuilt nightly by the dashboard scheduled
task. Each manifest entry carries `date`, `headline`, and
`latestTldrHtml` (the TL;DR card snapshot rendered on the home view).
Newsletters are loaded into a single `<iframe>` — no page-to-page
navigation. Hash routing (`#economy/2026-05-15`, `#home`) makes the back
button work, and `<base target="_blank">` in each newsletter ensures
in-content links escape the iframe.

### Constraints worth remembering

- No inline `<style>` and no inline `<script>` inside `<body>`
  (exception: `<script type="application/json" id="…">` data blocks
  for Chart.js / benchmark / mermaid components).
- All canvases sit inside a wrapper with explicit height — Chart.js
  + `maintainAspectRatio: false` inside a flex parent triggers an
  infinite resize loop.
- A category's accent change is a single edit in `lib/tokens.css`.
  No daily file should hard-code an accent colour.

## Deployment — Cloudflare Pages → briefs.danieldeusing.de

The site is served publicly at **https://briefs.danieldeusing.de** from a
**Cloudflare Pages** project named `briefs` (production branch `prod`). No Docker,
no Caddy, no Tailscale — the previous tailnet-only `news.twiced.de` setup was
decommissioned (it broke on every power outage / VPN hiccup; Cloudflare Pages is
public, free, and zero-maintenance).

### How it deploys

`tools/deploy-cloudflare.sh` is the single deploy entrypoint:

```bash
bash tools/deploy-cloudflare.sh        # wraps: wrangler pages deploy public \
                                       #   --project-name briefs --branch prod
```

It reads the Cloudflare **Pages-Edit** API token + Account ID — primarily
straight from the workspace `.env` (keys `CLOUDFLARE_API_TOKEN` /
`CLOUDFLARE_ACCOUNT_ID`, op-free), falling back to 1Password (`OP_SERVICE_TOKEN`
→ vault `danieldeusing-agents`, item `cloudflare - daniedeusing - api token`)
only if they're absent — exports them, and runs `wrangler`. The `.env`-first path
exists because `op` intermittently **hangs in headless/cron runs**, which used to
silently stall the deploy and leave the live site stale. Nothing is hard-coded or
committed (`.env` is untracked, `chmod 600`). Runnable by hand or by the routine.

The consolidated **morning-brief routine runs this automatically** as its final
phase: rebuild dashboard → `git add -A && git commit && git push origin main` →
`bash tools/deploy-cloudflare.sh`. So every daily run publishes itself; a manual
deploy is only needed for an out-of-band change.

### Cloudflare wiring (already set up — reference)

- **Pages project:** `briefs`, subdomain `briefs-k4j.pages.dev`, prod branch `prod`.
- **Custom domain:** `briefs.danieldeusing.de` — a **proxied CNAME** to
  `briefs-k4j.pages.dev` in the `danieldeusing.de` zone (same pattern as
  `seedr.danieldeusing.de`). The DNS record was created with the
  `cloudflare - danieldeusing - dns token` (the Pages token can't edit DNS).
- **Caching:** Cloudflare Pages sets sane cache headers and busts on each deploy,
  so the stale-`index.html` problem of the old Caddy setup is gone — no per-file
  `Cache-Control` tuning needed.

### Note: this repo does NOT touch pagr / danieldeusing.de

The **pagr** Astro site (`apps/pagr`, → danieldeusing.de) does **not** host the
briefs at all: `danieldeusing.de/news` **redirects** to `briefs.danieldeusing.de`
(the canonical site this routine deploys), so pagr needs no rebuild when new
briefs publish. This repo does not trigger, rebuild, or otherwise touch pagr —
there is no `post-commit` hook here anymore. The morning routine's only publish
actions are (1) commit + push to GitHub `main` and (2) deploy the standalone
`briefs.danieldeusing.de` (above).

### Leftover decommission (old news.twiced.de — twiced infra)

The `news-static` Docker container on ddStudio and its local Caddyfile are
**removed**. Two references on the **shared twiced/manufaktur** edge remain and
should be cleaned up via the manufaktur repo's normal PR + deploy flow (not from
here — that edge is shared prod and the danieldeusing token can't touch the
`twiced.de` zone):

- the `news.twiced.de { … }` block in `manufaktur/deploy/Caddyfile` (~line 213),
- the `news.twiced.de` DNS record in the `twiced.de` zone.

Until removed, `news.twiced.de` just 502s — harmless, since it was tailnet-only
and is fully replaced by `briefs.danieldeusing.de`.
