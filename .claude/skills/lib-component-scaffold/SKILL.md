---
name: lib-component-scaffold
description: >
  Scaffold a new interactive Morning Brief lib component end-to-end — the
  newsletter.js init function (wired to the registerComponent / parseJsonScript /
  pageLang / escapeHtml conventions), the de/en/pt/es i18n string map, the
  styles.css block, and the docs/COMPONENTS.md + docs/FORMAT.md entries — so you
  fill in behaviour, not boilerplate. Use this whenever you're adding a new
  interactive component to public/lib/ (a chart, a toggle, a calculator, a board,
  any `data-component`-driven widget), or when someone says "add a lib
  component", "new newsletter component", "scaffold a component", "wire up a new
  data-component", or starts building anything that needs JS init + CSS + i18n +
  docs in the shared lib. Reach for it before hand-writing the wiring — the five
  touch-points are identical every time and easy to half-do (a forgotten
  language, a class that doesn't match the data-component, a missing doc entry, a
  dead alias left behind).
---

# lib-component-scaffold

## Why this exists

Every interactive component in `public/lib/` is wired the same way, across five
places:

1. an **init function** in `newsletter.js` following the house conventions —
   registered via `registerComponent(name, fn)`, detected by
   `[data-component="…"]`, idempotent (a `dataset` guard), a silent no-op when
   its target isn't on the page, reading inline data via `parseJsonScript(id)`,
   theme colours via `cssColors()`, and escaping injected text via `escapeHtml`;
2. an **i18n map** for `de/en/pt/es` (chrome text resolved through `pageLang()`),
   because an EN/PT/ES brief must never surface German control labels;
3. a **CSS block** in `styles.css` using design tokens so the component tracks
   the per-category accent and dark mode automatically;
4. a **`docs/COMPONENTS.md`** entry (the markup contract routines copy);
5. a **`docs/FORMAT.md`** table row (which category uses it).

Doing this by hand is repetitive and — precisely because it's boilerplate — easy
to half-do. The jobs-board build, for instance, shipped with a CSS class alias
that didn't match what the routine emitted and had to be torn out later, and the
i18n map is exactly the kind of thing where one language quietly gets skipped.

This skill prints all five stubs, correctly wired to the conventions, so the only
thing left is the component's actual behaviour.

## Usage

```bash
python3 .claude/skills/lib-component-scaffold/scripts/scaffold.py <component-name> [--json] [--no-i18n]
```

- `<component-name>` — kebab-case (e.g. `weather-strip`). Becomes the
  `data-component` value, the CSS class root, and the camelCased init fn name —
  all three kept in sync, which is the mismatch that otherwise renders nothing.
- `--json` — the component reads an inline `<script type="application/json">`
  data block (like `fx-series` / `jobs-board`). Adds the `parseJsonScript`
  wiring. Omit for components that only enhance existing DOM.
- `--no-i18n` — skip the i18n map (only if the component has zero user-facing
  chrome text — rare).

The script **prints** the stubs and tells you which file each goes in; it writes
nothing. Paste each into place, then implement the behaviour.

## After scaffolding

Implement the `// TODO` in the init function and the CSS, fill the i18n keys, and
complete the doc entries. Then run through the checklist the script prints —
especially:

- **The `data-component` value, the JS query, and the CSS class must all be the
  same string.** A mismatch is silent: the component just doesn't render (this is
  the exact bug the jobs-board alias caused).
- **Every i18n key filled for all four languages.**
- **Verify on `:8090`** (fresh lib via no-cache), never `:8765` (stale lib).
  Start the server first: `python3 tools/serve_local.py &` (on-demand now — the
  old always-on Docker edge is gone). If the component has layout, the
  `responsive-spacing-check` skill measures it across breakpoints; for visuals use
  `preview_screenshot`.

## Conventions reference

If you need to see the established patterns the stubs follow, read these in
`public/lib/newsletter.js`: `registerComponent` + the bootstrap loop (top),
`parseJsonScript`, `pageLang` + `UI_STRINGS`, `cssColors`, `escapeHtml`, and any
existing `init*` function (`initJobsBoard` is a full JSON-driven example;
`initFootnotes` is a DOM-enhancement example). The stub mirrors these — match
them and the component drops into the existing system cleanly.

## What this is NOT

It scaffolds the wiring for ONE component; it doesn't design the component or
write its behaviour, and it doesn't edit files (it prints stubs to paste). It's
the "never forget a touch-point again" tool, not a code generator for the actual
logic.
