---
name: family-event-radar
description: >
  Sweep a fixed set of event sources around Ribeirão Claro/PR for the FAMILY
  newsletter and return candidate family/kid events filtered to date>=today and
  ranked by distance ring (Kern ~50km → Day-trip ~150km → Londrina ~110km → São
  Paulo 4–6h), ready to drop into the brief's activity-table (Wann · Wo+Entfernung
  · Was · Eignung · Preis · Quelle). Reach for it whenever you're building the
  family brief's event/activity section, or you catch yourself about to run the
  same half-dozen ad-hoc searches across local + Londrina + SP feeds and then
  hand-reject the stale or past-dated hits. Triggers: "build the family event
  radar", "sweep family events", "what's on near Ribeirão Claro / Londrina / São
  Paulo this weekend", "find kid events for the family brief", "fill the family
  activity-table", "any family events this week", "Wochenend-Events für die
  Familie". Family-newsletter-specific tooling — it fetches and ranks source
  material; it is NOT a general research agent and does not write the event rows
  itself (you do, from what it returns).
---

# family-event-radar

## Why this exists

Daniel's family wants **things to do**, and the events that fill a good family
brief are scattered across four very different distance bands: what's on tonight
in Jacarezinho, a Saturday in Ourinhos, the SESC programme an hour away in
Londrina, and the occasional big São Paulo weekend trip. Pulling that together by
hand means running the same ad-hoc searches every morning, then squinting at each
result to throw out the ones that are stale (a Londrina "agenda" page that's
actually from February) or already past (a SESC "Domingo em Família" that happened
last Sunday). That hand-filtering is exactly where a real event slips through or a
dead one sneaks in.

This skill pins down the two parts of that work that are **mechanical** — *where to
look* (a fixed, ranked source set) and *what to throw out* (anything dated before
today, sorted near-to-far) — so every run starts from the same trustworthy sweep
instead of re-improvising it. It does the boring, reliable thing; you do the
reading.

## The boundary — what this skill does and does NOT do

This mirrors the deliberate split in `jobs-prefs-apply`: the script owns the
deterministic part, you own the judgement.

- **The skill DOES:** fetch each fixed source page (surviving 403 / PDF / JS-shell
  the same way `fetch-with-fallback` does), tag each with its ring + distance
  label + URL, and — once you've assembled events — drop past-dated ones and rank
  by ring. That's pure IO + date arithmetic; it can't drift.
- **The skill does NOT:** parse event prose out of a page. Event listings are
  free-form HTML in four different site layouts; a regex would be brittle and
  would silently miss things. So `sweep` hands you each page's **text** and you
  read the events out of it — you have the judgement to tell "Festa Junina, Sat
  24th, free, all ages" from a navbar link. The skill has no opinion on text it
  hasn't parsed, and won't pretend to.

Keeping that line honest is the whole point: the script never fabricates an event,
and you never re-derive the date/ring filter from a paragraph.

## Two steps

### 1. `sweep` — fetch the fixed source set, near→far

```bash
cd /Users/daniel/Work/danieldeusing/morning-briefs/daniel
python3 .claude/skills/family-event-radar/scripts/event_radar.py sweep
```

Reads `sources/family-events.json` (the fixed source set, grouped by ring) and
prints JSON: `today`, counts, and one block per source with `ring`, `distance`,
`source_url`, and either `text` (the fetched page, capped at 20k chars) or
`error` (why it was skipped — `HTTP 403`, `JS shell`, etc.). **Read each `ok:true`
block's text and extract the family/kid events.** For an `ok:false` source, open
it by hand or omit it — never invent events for a source that didn't load.

For each event you find, assemble a dict:

```json
{ "date": "2026-05-24", "ring": "sp-range", "distance": "4–6 h (Großraum SP)",
  "was": "Virada Cultural — 24 h Kultur, Kinder-Block", "eignung": "alle Altersstufen",
  "preis": "gratis", "quelle": "https://passeioskids.com/virada-cultural-passeios-kids/" }
```

`ring` must be one of `kern | day-trip | londrina | sp-range` (the same keys the
config uses) so step 2 can rank it.

### 2. `filter` — drop past-dated events, rank by ring (THE GUARD)

Pipe your assembled list back through the script:

```bash
echo '[ ...your event dicts... ]' \
  | python3 .claude/skills/family-event-radar/scripts/event_radar.py filter
# or: --events events.json
```

It returns `kept` (date≥today, sorted by ring then date — drop straight into the
activity-table top-to-bottom), `dropped` (with a reason like `past-dated
(2026-05-17 < 2026-05-20)`), and `flagged` (events it kept but you must look at —
an unparseable date or an unknown ring). Today comes from the system clock; never
pass `--today` except in tests.

Why a separate step instead of trusting yourself to filter while reading: the
sweep returns pages that openly mix old and new (a cultural-agenda page lists last
month's shows above this week's). Running every candidate through one date gate in
code is what stops a past-dated event reaching the brief — the precise mistake
this skill exists to kill.

## Maintaining the source set

`sources/family-events.json` is the fixed where-to-look list, grouped by ring and
ordered near→far (that order *is* the ranking). Add or swap sources as you find
better local feeds — keep each under the correct ring so distance ranking stays
right, and set `kind` to `pdf` for a source that serves a PDF (the fetcher will
run `pdftotext`). Social handles that have no crawlable page (an Instagram feed)
don't belong here as fetch rungs; note them in the family `SKILL.md` events
section as "check by hand" instead.

## Verifying it (fixture, no live web needed)

`fixtures/events-sample.json` is a hand-built candidate list spanning all four
rings, deliberately out of order, with one past-dated event and one unknown-ring
event. Run the guard against a fixed "today" so the result is stable:

```bash
cd /Users/daniel/Work/danieldeusing/morning-briefs/daniel
python3 .claude/skills/family-event-radar/scripts/event_radar.py filter \
  --events .claude/skills/family-event-radar/fixtures/events-sample.json \
  --today 2026-05-20
```

**Expected:** exit 0, and:
- `kept_count` = **5**, `dropped_count` = **1** (6 events in: 1 past-dated is
  dropped, the other 5 are future-dated and kept).
- The one event dated `2026-05-17` (past) is in `dropped` with a `past-dated` reason.
- `kept` is ordered **kern → day-trip → londrina → sp-range** (the EnCena "Cícera"
  kern event first).
- The event with `ring: "mars"` is future-dated, so it's **kept** (a real future
  event isn't dropped just for an odd ring) but appears in `flagged` with an
  "unknown ring" warning and sorts last among kept. That split — drop only on
  *date*, merely *flag* an unknown ring — is deliberate: a date in the past is a
  hard disqualifier, but an unrecognised ring is a labelling slip you should see
  and fix, not lose the event over.

If those hold, the deterministic core is sound; the rest is your reading of the
swept pages.
