---
name: dashboard-consistency-check
description: >
  Verify every Morning Brief dashboard category is fully wired for its accent
  colour across tokens.css and index.html. Run this AFTER adding a new category
  to tools/build_manifest.py's CATEGORIES list, or whenever someone says "check
  dashboard consistency", "did I wire the new category", "why is the dashboard
  showing the wrong colour", or touches the per-category accent CSS. Catches the
  silent desync where a category falls back to the default economy-red accent
  because one of its four required definitions is missing. Use it proactively
  any time the category set changes — the failure is invisible until someone
  looks at the rendered dashboard.
---

# Dashboard consistency check

## Why this exists

The dashboard gives each newsletter category its own accent colour. That colour
only shows up if **four** definitions all exist for the category id. Three of
them live in `public/lib/tokens.css` and two in `public/index.html`'s inline
`<style>` — and those lists are hand-maintained, hardcoded per category. When
`motorsport` and `stocks-crypto` were added, their tokens existed but the
`index.html` accent rule and sidebar swatch did **not**, so both rendered with
the `:root` default (economy red) in the home cards and showed an invisible
(transparent) colour swatch in the sidebar. Nothing errors — it just looks
wrong, and only a human eyeballing the rendered dashboard would notice.

This skill turns that "eyeball the dashboard" step into a deterministic check so
adding category #11 (and beyond) can't reintroduce the bug.

## The four required definitions

For each category id `<X>` in `build_manifest.CATEGORIES`:

| # | File | What | Pattern |
|---|------|------|---------|
| 1 | `lib/tokens.css` | accent token | `--c-<X>: #…;` |
| 2 | `lib/tokens.css` | text-safe accent | `--c-<X>-text: …;` |
| 3 | `lib/tokens.css` | body alias | `body.cat-<X> { --accent: …; --accent-text: …; }` |
| 4 | `index.html` | home-card accent | `.tldr-card[data-cat="<X>"] { --accent: …; --accent-text: …; }` |
| 5 | `index.html` | sidebar swatch | `[data-cat="<X>"] .cat-color { background: …; }` |

(Five regex checks; "four definitions" colloquially, since the two tokens in
`tokens.css` are one logical accent pair. Note the dark-mode `@media` and
`[data-theme]` blocks in `tokens.css` also re-state `--c-<X>` / `--c-<X>-text`
— if the light-block token is present the dark ones almost always are too, so
the checker keys off the light `:root` block as the canonical signal.)

## How to run it

```bash
cd /Users/daniel/Work/danieldeusing/morning-briefs/daniel
python3 .claude/skills/dashboard-consistency-check/scripts/check_consistency.py
```

The script imports `tools/build_manifest.py` to read `CATEGORIES` directly (so
it can never drift from the builder's own list), then greps the five locations.
It prints a per-category table of ✓/✗ and exits **0** if every category is fully
wired, **1** if any definition is missing.

## Interpreting the result

- **All ✓, exit 0** — every category is wired. Done.
- **Any ✗, exit 1** — the script lists each missing definition with the exact
  file to edit, and names a fully-wired category to copy the pattern from. Fix
  by adding the missing rule(s), mirroring the example category in the same
  file, then re-run until green.

The colour values are the new category's call (pick a hue distinct from the
existing accents — see the palette table in `docs/FORMAT.md`). The skill checks
that the definitions *exist*, not what colour they are.

## After fixing

A consistency pass is necessary but not sufficient — it proves the wiring
exists, not that it renders. For a real new category, also rebuild the manifest
(`python3 tools/build_manifest.py`) and load the dashboard to confirm the card +
sidebar swatch show the intended colour. The accompanying `build_manifest.py
--verify` flag covers the manifest side (JSON valid, all categories present,
balanced tags); this skill covers the accent-wiring side. Run both when a
category changes.
