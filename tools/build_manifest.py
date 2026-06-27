#!/usr/bin/env python3
"""Rebuild window.__MANIFESTS in public/index.html with embedded TL;DR HTML."""
import os
import re
import json
import sys
from pathlib import Path
from datetime import date
from html import unescape

# Script lives in tools/, served content lives in ../public/.
BASE = Path(__file__).resolve().parent.parent / "public"
INDEX = BASE / "index.html"
# Standalone machine-readable manifest for OTHER sites (e.g. danieldeusing.de /briefs),
# committed to GitHub + deployed alongside the dashboard so they fetch structured data
# instead of scraping window.__MANIFESTS out of index.html.
MANIFEST_JSON = BASE / "manifest.json"

# Order mirrors the dashboard's grouped nav (Wirtschaft / IT / jobs / Sport /
# Freizeit / Sprachen). The grouping itself lives in index.html (NAV_GROUPS);
# this flat order is the canonical sequence the manifest + home grid follow.
CATEGORIES = [
    ("economy",        "Wirtschaft & Märkte", "📈", "var(--c-economy)"),
    ("stocks-crypto",  "Börse & Krypto",      "💰", "var(--c-stocks-crypto)"),
    ("software",       "Software & IT",       "🔧", "var(--c-software)"),
    ("ai-dev",         "AI fürs Coding",      "🤖", "var(--c-ai-dev)"),
    ("ai-usecases",    "AI in der Anwendung", "🏭", "var(--c-ai-usecases)"),
    ("jobs",           "Jobs & Aufträge",     "💼", "var(--c-jobs)"),
    ("football",       "Fußball",             "⚽", "var(--c-football)"),
    ("motorsport",     "Motorsport",          "🏎", "var(--c-motorsport)"),
    ("family",         "Familie & Region",    "🏡", "var(--c-family)"),
    ("learn-language", "Sprachen lernen",     "🗣", "var(--c-learn-language)"),
]

# Languages in order of preference for headline/TL;DR fallback. DE is canonical
# (always present); the others may or may not have a file for a given date.
LANGS = ["de", "en", "pt", "es"]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.html$")
# Opening <section …> tag whose class attribute contains "tldr" as a whole
# space-delimited token, regardless of order or sibling classes ("tldr foo",
# "x tldr"). The inner HTML and the matching </section> are found separately
# in extract_tldr_html so a nested <section> can't truncate the capture.
TLDR_OPEN_RE = re.compile(
    r'<section\b[^>]*\bclass\s*=\s*"[^"]*(?<![\w-])tldr(?![\w-])[^"]*"[^>]*>',
    re.IGNORECASE,
)
SECTION_TAG_RE = re.compile(r'<(/?)section\b', re.IGNORECASE)
# <h1>/<div> masthead title, tolerant of class-token order. "masthead-title"
# must be a whole class token (not a substring of a longer name).
TITLE_RE = re.compile(
    r'<(h1|div)\b[^>]*\bclass\s*=\s*"[^"]*(?<![\w-])masthead-title(?![\w-])[^"]*"[^>]*>(.*?)</\1>',
    re.DOTALL | re.IGNORECASE,
)
HTML_TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'\s+')
# Standfirst paragraph (<p class="lead">…</p>) — the brief's opening summary,
# used as the short teaser in the external manifest. "lead" must be a whole
# class token (not a substring of "leading" etc.).
LEAD_RE = re.compile(
    r'<p\b[^>]*\bclass\s*=\s*"[^"]*(?<![\w-])lead(?![\w-])[^"]*"[^>]*>(.*?)</p>',
    re.DOTALL | re.IGNORECASE,
)


def list_entries(cat_id: str):
    """Return a date-keyed map {date: {lang: Path}} for every category, looking
    inside each language subfolder. Dates with at least one language version
    are returned, sorted newest-first."""
    by_date: dict[str, dict[str, Path]] = {}
    for lang in LANGS:
        folder = BASE / cat_id / lang
        if not folder.exists():
            continue
        for p in folder.iterdir():
            if not DATE_RE.match(p.name):
                continue
            datestr = p.stem
            by_date.setdefault(datestr, {})[lang] = p
    # newest-first
    return sorted(by_date.items(), key=lambda kv: kv[0], reverse=True)


def extract_headline(html: str) -> str:
    m = TITLE_RE.search(html)
    if m:
        text = HTML_TAG_RE.sub('', m.group(2))
        return WS_RE.sub(' ', text).strip()
    m2 = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    if m2:
        return WS_RE.sub(' ', m2.group(1)).strip()
    return ""


def extract_tldr_html(html: str) -> str:
    m = TLDR_OPEN_RE.search(html)
    if not m:
        return ""
    # Walk <section>/</section> tags from just after the opening tag, tracking
    # nesting depth, so a nested <section> inside the TL;DR doesn't end the
    # capture early at the first </section>.
    depth = 1
    pos = m.end()
    for tag in SECTION_TAG_RE.finditer(html, pos):
        if tag.group(1):          # </section>
            depth -= 1
            if depth == 0:
                inner = html[pos:tag.start()].strip()
                # Wrap in <div class="tldr"> so the dashboard's existing CSS
                # rules (.tldr-card-body .tldr ul/li/chip styles) target the
                # embedded content.
                return f'<div class="tldr">{inner}</div>'
        else:                     # nested <section ...>
            depth += 1
    # Unbalanced markup (opening tag with no matching close) — skip.
    return ""


def extract_summary(html: str, max_chars: int = 200) -> str:
    """Plain-text teaser from the brief's <p class="lead"> standfirst, trimmed
    to a clean ~2-line length: prefer a sentence boundary, else a word boundary
    with an ellipsis. Returns "" when the brief has no lead paragraph."""
    m = LEAD_RE.search(html)
    if not m:
        return ""
    text = unescape(WS_RE.sub(' ', HTML_TAG_RE.sub('', m.group(1))).strip())
    if len(text) <= max_chars:
        return text
    head = text[:max_chars]
    for sep in ('. ', '! ', '? '):
        idx = head.rfind(sep)
        if idx > max_chars * 0.5:
            return head[:idx + 1].strip()
    return head.rsplit(' ', 1)[0].rstrip(' ,;:—-') + '…'


def build_manifest():
    categories = []
    for cat_id, label, icon, color in CATEGORIES:
        dated_files = list_entries(cat_id)
        entries = []
        latest_tldr_by_lang: dict[str, str] = {}
        headline_by_lang_latest: dict[str, str] = {}
        for i, (datestr, lang_files) in enumerate(dated_files):
            # Headlines: capture one per language present for this date so the
            # dashboard list can show the chosen language's headline (falling
            # back to DE in JS when a translation is missing).
            entry_headlines: dict[str, str] = {}
            # Standfirst teasers, captured only for the latest issue (i == 0) —
            # the external manifest only surfaces the newest one per category.
            entry_summaries: dict[str, str] = {}
            for lang, path in lang_files.items():
                try:
                    html = path.read_text(encoding="utf-8")
                except Exception:
                    continue
                entry_headlines[lang] = extract_headline(html)
                if i == 0:
                    latest_tldr_by_lang[lang] = extract_tldr_html(html)
                    headline_by_lang_latest[lang] = entry_headlines[lang]
                    entry_summaries[lang] = extract_summary(html)
            entries.append({
                "date": datestr,
                # canonical fallback used by the dashboard when the active
                # language has no translation for this date
                "headline": entry_headlines.get("de", next(iter(entry_headlines.values()), "")),
                "headlines": entry_headlines,
                "summaries": entry_summaries,
                "langs": sorted(lang_files.keys()),
            })
        cat_obj = {
            "id": cat_id,
            "label": label,
            "icon": icon,
            "color": color,
            "entries": entries,
        }
        if latest_tldr_by_lang:
            cat_obj["latestTldrHtml"] = latest_tldr_by_lang.get(
                "de", next(iter(latest_tldr_by_lang.values()), ""),
            )
            cat_obj["latestTldrHtmlByLang"] = latest_tldr_by_lang
        categories.append(cat_obj)

    today = date.today().isoformat()
    return {"generated": today, "categories": categories}


def build_external_manifest(manifest: dict) -> dict:
    """A slim, stable manifest for external consumers (danieldeusing.de /briefs and
    anyone else): per-category id/label/icon, the latest issue date, the entry count,
    and the latest headline per language — no embedded TL;DR HTML, so it stays small
    enough to fetch on every page load. Written to public/manifest.json."""
    all_dates = sorted({e["date"] for c in manifest["categories"] for e in c["entries"]})
    return {
        "generated": manifest["generated"],
        "since": all_dates[0] if all_dates else None,
        "latest": all_dates[-1] if all_dates else None,
        "languages": LANGS,
        "categories": [
            {
                "id": c["id"],
                "label": c["label"],
                "icon": c["icon"],
                "latest": c["entries"][0]["date"] if c["entries"] else None,
                "count": len(c["entries"]),
                "headline": c["entries"][0]["headlines"] if c["entries"] else {},
                "summary": c["entries"][0].get("summaries", {}) if c["entries"] else {},
            }
            for c in manifest["categories"]
        ],
    }


def render_js_literal(obj) -> str:
    """JSON is valid JS — emit pretty JSON for window.__MANIFESTS."""
    return json.dumps(obj, ensure_ascii=False, indent=2)


def splice_into_index(manifest_js: str):
    text = INDEX.read_text(encoding="utf-8")
    # Replace the block: window.__MANIFESTS = { ... };
    pattern = re.compile(
        r"(window\.__MANIFESTS\s*=\s*)(\{.*?\})(\s*;)",
        re.DOTALL,
    )
    if not pattern.search(text):
        print("ERROR: could not locate window.__MANIFESTS block", file=sys.stderr)
        sys.exit(1)
    new_text = pattern.sub(
        lambda m: m.group(1) + manifest_js + m.group(3),
        text,
        count=1,
    )
    tmp = INDEX.with_suffix(".html.tmp")
    tmp.write_text(new_text, encoding="utf-8")
    os.replace(tmp, INDEX)


MANIFEST_RE = re.compile(
    r"window\.__MANIFESTS\s*=\s*(\{.*?\})\s*;",
    re.DOTALL,
)


def verify_index() -> int:
    """Read-only sanity check of the manifest already spliced into index.html.
    Asserts the things a hand-check would: JSON parses, every CATEGORY id is
    present in declared order, `generated` is today, each entry carries a langs
    list containing 'de', and the document's <style>/<script> tags are balanced
    (a stray unclosed block would break the whole dashboard). Returns the number
    of failures (0 = OK) and prints a per-check report.
    """
    failures = []
    if not INDEX.exists():
        print("ERROR: index.html not found", file=sys.stderr)
        return 1
    text = INDEX.read_text(encoding="utf-8")

    m = MANIFEST_RE.search(text)
    if not m:
        print("  [✗] window.__MANIFESTS block not found")
        return 1
    try:
        manifest = json.loads(m.group(1))
        print("  [✓] manifest JSON parses")
    except json.JSONDecodeError as exc:
        print(f"  [✗] manifest JSON invalid: {exc}")
        return 1

    expected_ids = [cat_id for cat_id, *_ in CATEGORIES]
    actual_ids = [c.get("id") for c in manifest.get("categories", [])]
    if actual_ids == expected_ids:
        print(f"  [✓] all {len(expected_ids)} categories present, in order")
    else:
        failures.append("categories")
        print(f"  [✗] category mismatch:\n        expected {expected_ids}\n        actual   {actual_ids}")

    today = date.today().isoformat()
    if manifest.get("generated") == today:
        print(f"  [✓] generated == today ({today})")
    else:
        failures.append("generated")
        print(f"  [✗] generated is {manifest.get('generated')!r}, expected today {today!r}")

    bad_langs = []
    for c in manifest.get("categories", []):
        for e in c.get("entries", []):
            langs = e.get("langs")
            if not isinstance(langs, list) or "de" not in langs:
                bad_langs.append(f"{c.get('id')}/{e.get('date')}")
    if bad_langs:
        failures.append("langs")
        shown = ", ".join(bad_langs[:5]) + (" …" if len(bad_langs) > 5 else "")
        print(f"  [✗] {len(bad_langs)} entr{'y' if len(bad_langs)==1 else 'ies'} missing 'de' in langs: {shown}")
    else:
        print("  [✓] every entry's langs includes 'de'")

    # Real document tags only (a leading word boundary excludes the substring
    # hits inside JS strings/comments like "latestTldrHtml" or "print-dialog").
    for tag in ("style", "script"):
        o = len(re.findall(r"<%s\b" % tag, text))
        c = len(re.findall(r"</%s>" % tag, text))
        if o == c:
            print(f"  [✓] <{tag}> tags balanced ({o}/{c})")
        else:
            failures.append(f"{tag}-tags")
            print(f"  [✗] <{tag}> tags UNBALANCED ({o} open / {c} close)")

    if failures:
        print(f"\nFAIL: {len(failures)} check(s) failed: {', '.join(failures)}", file=sys.stderr)
    else:
        print("\nOK: manifest in index.html is consistent.")
    return len(failures)


def main():
    if "--verify" in sys.argv[1:]:
        sys.exit(1 if verify_index() else 0)
    manifest = build_manifest()
    js_literal = render_js_literal(manifest)
    splice_into_index(js_literal)
    # Standalone manifest for external consumers (committed + deployed with the site).
    MANIFEST_JSON.write_text(
        json.dumps(build_external_manifest(manifest), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    n_total = sum(len(c["entries"]) for c in manifest["categories"])
    today = manifest["generated"]
    new_today = sum(
        1 for c in manifest["categories"]
        for e in c["entries"] if e["date"] == today
    )
    print(f"Dashboard aktualisiert. {n_total} Newsletter erfasst ({new_today} heute neu).")
    for c in manifest["categories"]:
        has_tldr = "✓" if c.get("latestTldrHtml") else "✗"
        print(f"  [{has_tldr}] {c['id']:13s} {len(c['entries'])} entries")


if __name__ == "__main__":
    main()
