---
name: fetch-with-fallback
description: >
  Resiliently fetch a single live data point (FX rate, government-PDF statistic,
  benchmark score, sports standing) for a Morning Brief routine by stepping down
  an ordered ladder of sources — and return the value WITH its source URL and
  sample date. Use this whenever a routine needs a real number from the web and
  you want it to survive a 403, a PDF where you expected HTML, a JavaScript-only
  page, or a layout change that breaks your selector. Reach for it any time you
  catch yourself about to hardcode, guess, or carry over yesterday's figure
  because "the fetch didn't work" — the whole point is to try the next
  trustworthy source instead of fabricating. Triggers: "fetch the ECB rate",
  "get the dengue count from the gov PDF", "pull the SWE-Bench score", "the
  source is 403ing", "this page is JS-rendered", "add a fallback source",
  "EUR/BRL for today's brief", "scrape the standings". Especially relevant for
  economy (FX), family (gov PDFs), ai-dev (benchmark leaderboards) — but useful
  for any sourced number.
---

# fetch-with-fallback

## Why this exists

Every newsletter routine pulls live numbers, and those fetches fail in boring,
predictable ways: a `403`, a binary PDF served where you expected HTML, an empty
JS shell that only renders client-side, or a site that quietly changed its markup
so your selector now matches nothing. When that happens, the tempting shortcuts
are all wrong — hardcoding a value, eyeballing a guess, or silently reusing
yesterday's number. Those produce a brief that *looks* sourced but isn't, and the
economy brief-gate will (rightly) **block** an undated or fabricated FX series.

The honest, durable move is to try the **next** trustworthy source. This skill
turns "the fetch broke" into "fall through to the fallback" — and it returns the
value together with the URL it came from and the date it was sampled, so the rest
of the pipeline can cite it truthfully. If *every* source fails, it tells you
exactly why each one failed so you can decide to **omit the figure** rather than
invent one.

## The engine

`scripts/fetch_engine.py` (stdlib only; uses `pdftotext` for PDF rungs if it's
installed). You give it a **ladder** — an ordered list of sources — and it
returns the first one that yields a value:

```bash
# A config file maps metric → ladder; fetch one metric:
python3 .claude/skills/fetch-with-fallback/scripts/fetch_engine.py \
    .claude/skills/fetch-with-fallback/sources/economy-fx.json --key eurbrl
```

Success prints:

```json
{
  "ok": true,
  "value": "5.8347",
  "source_url": "https://www.ecb.europa.eu/.../eurofxref-daily.xml",
  "source_name": "ECB euro reference rates (daily XML)",
  "rung": 0,
  "date": "2026-05-20",
  "date_inferred": false
}
```

All-fail prints `{"ok": false, "value": null, "attempts": [...]}` with a per-rung
reason, and exits 3.

**Use the result honestly:**
- `value` + `source_url` → the number and its citation link. Put both in the brief.
- `date` → the sample date. If `date_inferred` is `true`, the engine could NOT
  pull a date from the source (it filled in today's date as a placeholder). Treat
  an inferred date with suspicion: either find a source that exposes a real date,
  or label the figure's timing honestly. Never present an inferred date as if the
  source stated it — that's the exact thing the economy gate blocks.
- `ok: false` → do not fabricate. Omit the figure, or fall back to clearly-labeled
  "as of [last known date]" prose. Surface the `attempts` so the failure is visible.

## Writing a source ladder (for data-category owners)

A config is `{ "<metric>": [ <rung>, <rung>, ... ] }`. Order rungs **most
authoritative first**, fallbacks below. A rung:

```json
{
  "name": "human-readable source name",
  "url": "https://…",
  "kind": "json" | "html" | "pdf",
  "extract": { ... },
  "date_extract": { ... },          // optional but STRONGLY preferred
  "headers": { "User-Agent": "…" }  // optional
}
```

`extract` / `date_extract` by `kind`:

| kind   | extract spec                          | how it pulls the value |
|--------|---------------------------------------|------------------------|
| `json` | `{"path": "rates.BRL"}`               | dot/bracket path into parsed JSON (`data[0].score` works) |
| `html` | `{"regex": "id=\"x\">([0-9.,]+)"}`    | first capture group of the regex over the page text |
| `pdf`  | `{"regex": "Casos: ([0-9.]+)"}`       | first capture group over the `pdftotext -layout` output |

Notes that save you debugging:
- **XML counts as `html`** — point a regex at the tag/attribute (the ECB rung in
  `sources/economy-fx.json` regexes the `rate="…"` attribute out of the XML).
- **Always add `date_extract` if the source exposes a date.** A value with a real
  sample date is trusted; without one it's flagged `date_inferred` and is gate-bait.
- The engine **steps down on**: network error / 403, non-JSON when `kind=json`,
  a PDF body when `kind=html`, a detected JS shell, or a regex/path miss. So a rung
  that returns the wrong thing is treated as a failure, not a bad value — exactly
  what you want.
- Keep ladders in `sources/<category>-<topic>.json`. Reference config:
  `sources/economy-fx.json` (ECB XML → exchangerate.host JSON).

## Suggested ladders per category (owners fill these in)

- **economy** — `eurbrl`, `usdbrl` (ECB XML first; an open FX API as fallback),
  `dxy` (a dollar-index source + fallback). Started in `sources/economy-fx.json`.
- **family** — dengue / InfoGripe gov **PDFs** (`kind: pdf`), with the HTML
  landing page as a fallback rung if the PDF URL rotates.
- **ai-dev** — benchmark leaderboards: SWE-Bench, LiveCodeBench, LMArena. These
  are often JS-rendered — put a static/JSON endpoint first if one exists, the
  rendered page last (the engine will flag and skip a pure JS shell).

## What this skill is NOT

It fetches **one value at a time** over an explicit ladder you control. It is not
a general scraper, not a crawler, and not a research agent — it deliberately does
the narrow, reliable thing so a routine can trust the number it gets back. For
open-ended "find me sources about X", that's a research step, not this.
