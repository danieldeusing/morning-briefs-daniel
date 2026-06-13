---
name: srs-ledger-reconcile
description: >
  Make the learn-language spaced-repetition ledger
  (data/learn-language-ledger.json) agree with the day's brief by DERIVING its
  entry from the canonical DE file instead of hand-keeping a parallel list. Reads
  public/learn-language/de/<date>.html, extracts every vocab-item's German
  headword (lowercased — the ledger's canonical key form), and upserts the single
  entry for that date: replaces a same-date entry in place (never a duplicate
  date), carries theme/reviewed across, validates reviewed⊆headwords, enforces the
  ~120-entry cap. Run it at the END of a learn-language run once the DE file is
  final, or any time you're about to write/append the ledger entry by hand. Reach
  for it the moment you catch yourself typing a headword list into the ledger, or
  reconciling "what did today's brief actually teach" against the ledger — that
  hand step is exactly where the ledger drifts (a stale seed set, a duplicate date,
  a headword count that disagrees with the brief). Triggers: "reconcile the
  ledger", "update the SRS ledger", "append today's ledger entry", "does the ledger
  match the brief", "the ledger has the wrong words". learn-language-specific.
---

# srs-ledger-reconcile

## Why this exists

The learn-language newsletter teaches a set of headwords each day and records them
in a spaced-repetition ledger (`data/learn-language-ledger.json`), newest entry
first:

```json
{ "entries": [
    { "date": "YYYY-MM-DD", "theme": "…", "headwords": ["abholen", "der brei", …],
      "reviewed": ["abholen", …] }, … ] }
```

The routine reads this at the **start** of a run (skip words taught in the last ~14
days, pull 2–4 for review) and is supposed to record the day's set at the **end**.
The ledger only works if its headword list for a date is exactly what that date's
brief actually teaches. When it's hand-kept in parallel it drifts — and two drift
modes have both happened on real runs:

1. **STALE SET** — the 2026-05-20 entry once carried the *previous* day's 13
   headwords while the brief taught a different 33. The skip/review logic then
   reasons about words the reader never saw.
2. **DUPLICATE DATE / COUNT MISMATCH** — appending a second entry for the same date
   instead of replacing it, or a brief whose prose says "34 words" while it has 33
   items. Two entries for one date, or a count the brief contradicts.

The fix is to stop hand-keeping the list: the canonical DE file **is** the source
of truth, so the ledger entry should be *derived* from it. This skill does that
derivation deterministically, so the routine reconciles by running a script, not by
re-typing a word list.

## What it does

Reads the day's DE brief, pulls every vocab-item's German headword (the `<strong>`
inside `<div class="vocab-cell" lang="de">`, with the inline 🔊 button stripped),
lowercases it, and **upserts** the single ledger entry for that date:

- **Replace in place** if an entry for that date exists (no duplicate dates ever);
  insert at the front otherwise. Then sort newest-first and trim to ~120 entries.
- **`headwords`** comes entirely from the file, in teaching order — never hand-typed.
- **`theme`** and **`reviewed`** are editorial (not derivable from the HTML): on an
  in-place update they're **kept** from the existing entry unless you override them
  with `--theme` / `--reviewed`; on a brand-new entry they default to `""` / `[]`.
- **Validates `reviewed ⊆ headwords`** — a review word the brief never showed is a
  real inconsistency and hard-fails (exit 2), rather than being silently written.
- **Rejects duplicate headwords** in the file (they'd corrupt the skip set).

It deliberately does NOT pick the review words or invent a theme — those are
editorial calls the routine makes. It only guarantees the headword list mirrors the
brief and the structure is well-formed.

## How to run it

```bash
cd /Users/daniel/Work/danieldeusing/morning-briefs/daniel

# End-of-run reconcile: derive 2026-05-20's entry from its DE file, set the day's
# review words + theme, upsert the ledger.
python3 .claude/skills/srs-ledger-reconcile/scripts/reconcile_ledger.py \
  --reviewed "abholen,schlafen,müde,einen wutanfall bekommen" \
  --theme "Familie & Alltag (XL)" --pretty
```

With no `--file` it auto-discovers the **newest** `public/learn-language/de/<date>.html`.
With no `--reviewed` / `--theme` on an existing entry it keeps those fields as they
are (handy to re-derive only the headwords after editing the brief). Plain
`python3`, no third-party dependencies.

### Read-only pre-flight (`--check`)

```bash
python3 .claude/skills/srs-ledger-reconcile/scripts/reconcile_ledger.py --check --pretty
```

`--check` mutates nothing and exits **1** if the ledger entry would change (drift
detected) or there's a duplicate date, **0** if it's already consistent. Use it in a
gate or before reporting a run "done" to catch a ledger that no longer matches the
shipped brief.

### Exit codes

- **0** — write succeeded, or `--check` found the ledger already consistent.
- **1** — `--check` only: the entry does not match the file (drift). Re-run without
  `--check` to fix.
- **2** — hard error: DE file missing/unreadable, no vocab items found (wrong file
  or the markup changed), malformed ledger JSON, a duplicate DE headword, or a
  `--reviewed` word that isn't among the brief's headwords. These must be noticed,
  never silently written.

## Verifying it (fixture)

A self-contained fixture proves the upsert + validation without touching live data:

- `fixtures/de/2026-01-15.html` — a 2-item DE brief (teaches `kochen`, `die suppe`).
- `fixtures/ledger-stale.json` — a ledger whose 2026-01-15 entry deliberately holds
  the WRONG set (`backen`, `der ofen`, `das mehl`) plus an older 2026-01-14 entry.

```bash
cd /Users/daniel/Work/danieldeusing/morning-briefs/daniel
SK=.claude/skills/srs-ledger-reconcile
cp "$SK/fixtures/ledger-stale.json" /tmp/ledger-test.json

# 1) drift is detected (exit 1)
python3 "$SK/scripts/reconcile_ledger.py" --file "$SK/fixtures/de/2026-01-15.html" \
  --ledger /tmp/ledger-test.json --check ; echo "exit $?"

# 2) upsert in place, set review word + theme (exit 0, action "updated")
python3 "$SK/scripts/reconcile_ledger.py" --file "$SK/fixtures/de/2026-01-15.html" \
  --ledger /tmp/ledger-test.json --reviewed "kochen" --theme "Küche (XL)" --pretty

# 3) now consistent (exit 0); 2026-01-14 entry untouched, no duplicate 2026-01-15
python3 "$SK/scripts/reconcile_ledger.py" --file "$SK/fixtures/de/2026-01-15.html" \
  --ledger /tmp/ledger-test.json --check ; echo "exit $?"

# 4) a review word the brief never taught hard-fails (exit 2)
python3 "$SK/scripts/reconcile_ledger.py" --file "$SK/fixtures/de/2026-01-15.html" \
  --ledger /tmp/ledger-test.json --reviewed "fliegen" ; echo "exit $?"
```

After step 2 the 2026-01-15 entry reads `headwords: ["kochen", "die suppe"]`,
`reviewed: ["kochen"]`, `theme: "Küche (XL)"`, and the ledger still has exactly two
entries (newest-first), proving the in-place replace and that other dates survive.

## How the learn-language routine uses this

In the routine's closing "Ledger (Pflicht)" step, instead of hand-writing the day's
entry: finalize the DE file, then run this script with the day's `--reviewed` words
and `--theme`. It derives `headwords` from the file (so the ledger can never disagree
with the brief's count or set), upserts the single dated entry, and enforces the cap.
Pair it with the learn-language brief-gate module: `--check` is the pre-ship assertion
that the ledger and the shipped brief still agree.
