---
name: responsive-spacing-check
description: >
  Measure a CSS selector's computed box metrics (gap between siblings, width,
  height, font-size) and horizontal-overflow across multiple breakpoints AND
  multiple Morning Brief category pages in one pass, then print a comparison
  table that flags overflow, font-size inconsistency, and gap drift. Use this
  whenever you change something in public/lib/styles.css that affects layout or
  spacing — section gaps, font scale, grid columns, padding, a responsive rule —
  because a lib edit hits ALL ten categories in ALL four languages and eyeballing
  one page proves nothing. Reach for it when you'd otherwise resize the preview
  by hand and squint, or when someone says "is the spacing consistent", "does
  this overflow on mobile", "check this across breakpoints", "did my CSS change
  break any category", "verify the timeline font size", or after editing any
  shared `.col`/`.body-grid`/`.news-item`/`.timeline`/`.tldr` rule. Verifies on
  :8090 (fresh lib), not :8765 (stale).
---

# responsive-spacing-check

## Why this exists

A change in `public/lib/styles.css` is global: it renders in every one of the
ten categories, in four languages, at six breakpoints. So "I bumped the section
gap and it looks right on the economy page at 1280px" is not verification — it's
one of sixty-plus cells. The failures that hide in the other cells are exactly
the ones that bite: a gap that reads fine on a dense 3-column page but over-airs
a short 2-column one, a font-size that's consistent on one category but not
another, content that fits at 1280px but overflows at 380px.

This skill makes the numbers legible across that grid. You probe a selector on a
few representative pages at a few widths, and it prints one table plus a flags
section that calls out overflow, font mixing, and gap drift. It's a **report for
a judgment call**, not a gate — "the right amount of spacing" is taste, but you
should be making that call with the computed numbers in front of you, not a
single squint.

## Workflow

You drive the preview with the `mcp__Claude_Preview__preview_eval` /
`preview_resize` tools; this skill supplies the probe and the formatter.

0. **Start the local no-cache server on :8090** (it's on-demand now — the old
   always-on Docker edge is gone): `python3 tools/serve_local.py &` from the repo
   root. It serves `public/` with `Cache-Control: no-cache` on `/lib/*`. Leave it
   running for the whole check; stop it (kill the process) when done.

1. **Pick representative pages.** Don't do all 40 — pick ~3 that stress the
   selector differently. For a body-grid spacing rule: a dense 3-column category
   (`software` or `ai-dev`), a 2-column one (`jobs` or `family`), and one with a
   different content shape (`economy`). For a timeline rule, any 2–3 categories.

2. **Pick breakpoints.** The lib's responsive breaks are 1280 / 1100 / 900 / 720
   / 600 / 380 px. Probe at least one wide (1280), one mid (720), one phone (380),
   plus any breakpoint your change specifically targets.

3. **Probe each (page × width).** Resize, navigate to the page **on :8090**
   (`http://localhost:8090/<cat>/de/<date>.html` — :8090 sends no-cache on /lib/
   so your edit loads fresh; :8765 serves a STALE lib and will mislead you), then
   run the probe from `scripts/measure.js` with `SELECTOR` set to your target.
   Each run returns one JSON object. Collect them into an array.

   ```
   preview_resize({width: 1280, height: 900})
   preview_eval({expression: "location.href='http://localhost:8090/software/de/2026-05-20.html'"})
   preview_eval({expression: <contents of measure.js with SELECTOR replaced>})
   ```

   The preview is a single shared browser — re-assert the URL right before each
   probe in case it drifted, and confirm `port` in the result is `8090`.

4. **Tabulate.** Save the collected array to a file and run the formatter:

   ```bash
   python3 .claude/skills/responsive-spacing-check/scripts/tabulate.py results.json
   ```

   It prints a row per probe (page, width, match count, overflow px, gap min/max,
   the set of font-sizes) and a FLAGS section.

5. **Read the flags, make the call.** `OVERFLOW` = content wider than the
   viewport (almost always a real bug on phones). `FONT-MIX` = the matched
   elements don't share a size at that width (intended hierarchy, or drift?).
   `GAP-DRIFT` = a shared rule is producing different gaps across categories
   (usually means a selector isn't matching uniformly). `NO-MATCH` = selector
   typo or wrong page. `PORT` = you measured stale lib — redo on :8090.

## Example

Verifying a sub-story spacing change to `.col > section`:

```
SELECTOR = ".col > section.news-item"
pages    = software, jobs, economy
widths   = 1280, 720, 380
```

A clean result: gap ~48px at 1280/720, ~32px at 380 (a deliberate mobile
dial-back), one font-size per set, zero overflow, all on :8090. A bad result
would surface as an OVERFLOW flag at 380 or a GAP-DRIFT across categories.

## What this is NOT

It measures and reports — it does not change CSS and does not decide whether the
spacing is "good". It also doesn't screenshot (use `preview_screenshot` for a
visual). It's the quantitative half of a lib-layout review; your eye and taste
are the other half.
