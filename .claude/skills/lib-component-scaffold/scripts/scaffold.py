#!/usr/bin/env python3
"""lib-component-scaffold — emit the boilerplate for a new interactive lib component.

Adding an interactive component to public/lib/ means touching the SAME five
places every time, in a fixed pattern: a registerComponent() call + an init
function in newsletter.js (following the registry / parseJsonScript / pageLang /
escapeHtml conventions), an i18n string map for de/en/pt/es (or the EN/PT/ES
files surface German chrome), a CSS block in styles.css, and doc entries in
docs/COMPONENTS.md + docs/FORMAT.md. Doing this by hand is repetitive and easy to
half-do — a forgotten language in the i18n map, a CSS class that doesn't match
what the JS emits, a missing doc entry, a dead alias left behind.

This script prints all the stubs, correctly wired to the conventions, so you
fill in the BEHAVIOUR rather than rebuild the SCAFFOLDING. It writes nothing —
it prints to stdout for you to paste into the right files (and tells you where).

Usage:
    python3 scaffold.py <component-name> [--json] [--no-i18n]

  component-name : kebab-case, e.g. "weather-strip". Becomes the data-component
                   value, the CSS class root, and (camelCased) the init fn name.
  --json         : the component reads an inline <script type="application/json">
                   data block (like fx-series / jobs-board). Adds parseJsonScript
                   wiring. Omit for components that only enhance existing DOM
                   (like the voice-reader / footnotes).
  --no-i18n      : skip the i18n string map (component has no user-facing chrome
                   text). Most interactive components DO have chrome — keep i18n
                   unless you're sure.
"""
from __future__ import annotations

import re
import sys


def camel(name: str) -> str:
    parts = re.split(r"[-_]", name)
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def pascal(name: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[-_]", name))


def js_stub(name: str, use_json: bool, use_i18n: bool) -> str:
    fn = "init" + pascal(name)
    ui_block = ""
    ui_call = ""
    if use_i18n:
        ui_block = f"""
  // i18n chrome for this component. pageLang() resolves <html lang> → de|en|pt|es.
  // Fill EVERY language — an EN/PT/ES brief must not surface German control text.
  const {camel(name).upper()}_UI = {{
    de: {{ /* label: 'Beschriftung', */ }},
    en: {{ /* label: 'Label', */ }},
    pt: {{ /* label: 'Rótulo', */ }},
    es: {{ /* label: 'Etiqueta', */ }},
  }};
  function {camel(name)}Ui(key) {{ return ({camel(name).upper()}_UI[pageLang()] || {camel(name).upper()}_UI.de)[key]; }}
"""
        ui_call = f"    // const label = {camel(name)}Ui('label');\n"
    json_block = ""
    if use_json:
        json_block = f"""
    const data = parseJsonScript('{name}-data');   // <script type="application/json" id="{name}-data">
    if (!data) return;                              // no data block on this page → no-op
"""
    return f"""// ── {name} ──────────────────────────────────────────────────────────────
// Add near the other init functions in public/lib/newsletter.js, then register
// it (see the registerComponent line below). The function bails out silently if
// its target isn't on the page, so it's safe to ship on every brief.
{ui_block}
  function {fn}() {{
    const root = document.querySelector('[data-component="{name}"]');
    if (!root || root.dataset.{camel(name)}Bound) return;   // idempotent guard
    root.dataset.{camel(name)}Bound = '1';
{json_block}
    // Build/enhance the component here. Use escapeHtml(...) for any text you
    // inject as HTML. Read theme colours via cssColors() if you draw to canvas.
{ui_call}    // TODO: implement {name}.
  }}

  // Register (add alongside the other registerComponent calls near the bottom):
  registerComponent('{name}', {fn});
"""


def css_stub(name: str) -> str:
    return f"""/* ── {name} ──────────────────────────────────────────────────────────────
   Add to public/lib/styles.css. Use design tokens (var(--accent), var(--panel),
   var(--rule), var(--space-*), var(--text-*)) — never hard-code colours or px
   that a token covers, so the component tracks the per-category accent + dark
   mode for free. The container class MUST match the data-component value the JS
   queries ({name}) — a class/selector mismatch renders nothing and is silent. */
.{name} {{
  /* container layout */
}}
"""


def components_md_stub(name: str, use_json: bool) -> str:
    data = ""
    if use_json:
        data = f"""
<script type="application/json" id="{name}-data">
{{ /* component data; translate visible labels per file, keep ids/numbers identical */ }}
</script>"""
    return f"""## `{name}`

Used by: <category> · CDN: none · Slot: <where it goes>

```html
<section class="{name}" data-component="{name}"></section>{data}
```

<one or two sentences: what it renders and any attributes the routine sets.>
"""


def format_md_stub(name: str) -> str:
    return (f"| <category> | … · `{name}` … |   "
            f"# add `{name}` to this category's row in the component table")


def main(argv) -> int:
    if not argv:
        print(__doc__)
        return 2
    name = argv[0]
    if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
        print(f"component name must be kebab-case (got '{name}')", file=sys.stderr)
        return 2
    use_json = "--json" in argv
    use_i18n = "--no-i18n" not in argv

    print("=" * 72)
    print(f"SCAFFOLD for component '{name}'"
          f"{'  [+inline JSON]' if use_json else ''}"
          f"{'  [no i18n]' if not use_i18n else ''}")
    print("=" * 72)
    print("\n1) JS → paste into public/lib/newsletter.js")
    print("-" * 72)
    print(js_stub(name, use_json, use_i18n))
    print("\n2) CSS → paste into public/lib/styles.css")
    print("-" * 72)
    print(css_stub(name))
    print("\n3) docs/COMPONENTS.md → add a component entry")
    print("-" * 72)
    print(components_md_stub(name, use_json))
    print("\n4) docs/FORMAT.md → add to the 'which components fit which newsletter' table")
    print("-" * 72)
    print(format_md_stub(name))
    print("\n" + "=" * 72)
    print("CHECKLIST before you're done:")
    print(f"  [ ] data-component=\"{name}\" in the markup matches the JS query AND the CSS class .{name}")
    print(f"  [ ] init fn bails silently when [data-component=\"{name}\"] is absent (so other briefs are unaffected)")
    if use_i18n:
        print("  [ ] every i18n key filled for de/en/pt/es — no missing language")
    print("  [ ] CSS uses tokens (accent/panel/rule/space/text), no hard-coded colours")
    print("  [ ] COMPONENTS.md + FORMAT.md both updated; no dead class aliases left behind")
    print("  [ ] verified on :8090 (fresh lib), not :8765")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
