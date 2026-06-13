#!/usr/bin/env python3
"""Assert every Morning Brief dashboard category is fully wired for its accent.

A category renders with its own colour only if FOUR definitions all exist. If any
is missing, that category silently falls back to the :root default (economy red)
in the home cards / sidebar — the exact bug that hit motorsport + stocks-crypto
when they were added. This checker is the guard for the next category (#11).

The four required definitions, per category id <X> from build_manifest.CATEGORIES:
  1. lib/tokens.css   — `--c-<X>:` token         (the accent colour)
  2. lib/tokens.css   — `--c-<X>-text:` token    (the AA-safe text variant)
  3. lib/tokens.css   — `body.cat-<X> { … }`     (alias so newsletter pages pick it up)
  4. index.html       — `.tldr-card[data-cat="<X>"]` rule  (home-card accent scoping)
  5. index.html       — `[data-cat="<X>"] .cat-color` rule (sidebar swatch colour)

(That's 5 regex checks across 2 files; "four definitions" because the two tokens
are one logical pair.)

Exit code: 0 if every category passes all checks, 1 otherwise.
"""
import importlib.util
import re
import sys
from pathlib import Path

# repo root = three levels up from this script
# (.claude/skills/dashboard-consistency-check/scripts/check_consistency.py)
REPO = Path(__file__).resolve().parents[4]
BUILDER = REPO / "tools" / "build_manifest.py"
TOKENS = REPO / "public" / "lib" / "tokens.css"
INDEX = REPO / "public" / "index.html"


def load_category_ids():
    """Import build_manifest and read its CATEGORIES — the single source of truth
    for which categories exist. Importing (vs. re-parsing) means we never drift
    from the builder's own list."""
    spec = importlib.util.spec_from_file_location("build_manifest", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [cat_id for cat_id, *_ in mod.CATEGORIES]


def make_checks(cat_id: str):
    """Return {check_label: compiled_regex} for one category. The id is regex-
    escaped so a hyphenated id like `stocks-crypto` matches literally."""
    cid = re.escape(cat_id)
    return {
        "tokens.css --c-X":         (TOKENS, re.compile(r"--c-%s:\s*#" % cid)),
        "tokens.css --c-X-text":    (TOKENS, re.compile(r"--c-%s-text:\s*" % cid)),
        "tokens.css body.cat-X":    (TOKENS, re.compile(r"body\.cat-%s\b" % cid)),
        "index.html .tldr-card":    (INDEX,  re.compile(r'\.tldr-card\[data-cat="%s"\]' % cid)),
        "index.html .cat-color":    (INDEX,  re.compile(r'\[data-cat="%s"\]\s*\.cat-color' % cid)),
    }


def main():
    for path in (BUILDER, TOKENS, INDEX):
        if not path.exists():
            print(f"ERROR: missing {path}", file=sys.stderr)
            return 1

    ids = load_category_ids()
    tokens_text = TOKENS.read_text(encoding="utf-8")
    index_text = INDEX.read_text(encoding="utf-8")
    text_for = {TOKENS: tokens_text, INDEX: index_text}

    check_labels = list(make_checks(ids[0]).keys())
    # Header
    print(f"Dashboard category consistency — {len(ids)} categories\n")
    col = max(len(i) for i in ids) + 1
    short = ["--c-X", "-text", "cat-X", "card", "swatch"]
    print(f"{'category':<{col}}  " + "  ".join(f"{s:^7}" for s in short))
    print("-" * (col + 2 + 9 * len(short)))

    gaps = []
    for cat_id in ids:
        checks = make_checks(cat_id)
        row_marks = []
        for label, (path, rx) in checks.items():
            ok = bool(rx.search(text_for[path]))
            row_marks.append("✓" if ok else "✗")
            if not ok:
                gaps.append((cat_id, label, path))
        print(f"{cat_id:<{col}}  " + "  ".join(f"{m:^7}" for m in row_marks))

    print()
    if not gaps:
        print(f"OK: all {len(ids)} categories fully wired ({len(check_labels)} checks each).")
        return 0

    print(f"FAIL: {len(gaps)} missing definition(s):", file=sys.stderr)
    for cat_id, label, path in gaps:
        rel = path.relative_to(REPO)
        print(f"  • {cat_id}: missing {label}  →  add it in {rel}", file=sys.stderr)
    # A concrete hint, mirroring an existing wired category so the fix is copy-paste.
    example = next((i for i in ids if all(rx.search(text_for[p]) for _, (p, rx) in make_checks(i).items())), None)
    if example:
        print(f"\nCopy the pattern from a fully-wired category (e.g. '{example}') in the same file.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
