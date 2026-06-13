#!/usr/bin/env python3
"""Make the learn-language SRS ledger agree with the brief it ships alongside.

The learn-language newsletter teaches a set of headwords each day and records them
in a spaced-repetition ledger (`data/learn-language-ledger.json`) so the next run
can skip recently-taught words and resurface a few for review. The ledger's headword
list MUST match what the day's brief actually teaches — if it drifts (a seed entry
left from a prior run, a hand-typed list that's off by a word, a stray duplicate
date), the SRS logic silently rots: words get re-taught too soon, or "reviewed"
points at a headword the brief never showed.

That match is pure, deterministic extraction: the canonical DE file IS the source of
truth, so the ledger entry for its date should be *derived* from it, not hand-kept in
parallel. This script reads the DE file, pulls every vocab-item's German headword
(the `<strong>` inside `<div class="vocab-cell" lang="de">`), lowercases it (the
ledger key is the German canonical form, lowercased), and upserts the single entry
for that date — replacing an existing same-date entry in place rather than appending
a duplicate. It carries the entry's `theme` and `reviewed` list across an in-place
update (those are editorial, not derivable from the HTML), and validates that every
`reviewed` word is actually in the headword set.

Two bug classes this kills, both seen in real runs:
  1. STALE SET — the 2026-05-20 entry once held the previous day's 13 headwords while
     the brief taught a different 33. Re-deriving from the file makes that impossible.
  2. DUPLICATE DATE / COUNT MISMATCH — appending instead of upserting, or a prose
     headword count that disagrees with the actual items. One entry per date, count
     == the brief's vocab-item count, always.

Inputs (paths resolved against the repo root, overridable by flag):
  --file    public/learn-language/de/<date>.html   the canonical DE brief to read.
            When omitted, auto-discovers the NEWEST de/<date>.html.
  --ledger  data/learn-language-ledger.json         the ledger to upsert into.
  --reviewed w1,w2,...   comma-separated DE-canonical (lowercased) review words for
            this entry. Optional: when omitted, an in-place update keeps the existing
            entry's reviewed list; a brand-new entry starts with [].
  --theme   short theme label for the entry. Optional: kept from the existing entry on
            update, or "" on a new entry, unless given.

Modes:
  (default)   --write : perform the upsert and save the ledger.
  --check     read-only: report whether the ledger entry already matches the file
              (headwords + reviewed⊆headwords + single-date), exit 1 if it would
              change. Use this in a gate / pre-flight without mutating anything.

Output (stdout, JSON; --pretty for indented): a summary of what changed.

Exit codes:
  0  success (write done, or --check found the ledger already consistent)
  1  --check only: the ledger entry does NOT match the file (drift detected)
  2  a hard error: DE file missing/unreadable, no vocab items found, malformed
     ledger JSON, or a --reviewed word that isn't among the file's headwords.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# repo root = four levels up from .claude/skills/srs-ledger-reconcile/scripts/<this>.py
REPO = Path(__file__).resolve().parents[4]
LL_DIR = REPO / "public" / "learn-language"
DE_DIR = LL_DIR / "de"
DEFAULT_LEDGER = REPO / "data" / "learn-language-ledger.json"

DATE_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.html$")
LEDGER_CAP = 120

# A vocab-item's German headword lives in the de cell's <strong>, before the inline
# 🔊 button: <div class="vocab-cell" lang="de"> <strong>HEADWORD <button …>.
# Capture the cell, then the strong's leading text up to the <button>.
DE_CELL_RE = re.compile(
    r'<div\s+class="vocab-cell"\s+lang="de">\s*<strong>(.*?)</strong>',
    re.DOTALL | re.IGNORECASE,
)
BUTTON_SPLIT_RE = re.compile(r"<button\b", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def die(msg: str, code: int = 2):
    sys.stderr.write(f"ERROR: {msg}\n")
    sys.exit(code)


def rel(path: Path) -> str:
    """Path relative to the repo root for display, falling back to the resolved
    absolute path when it lives outside the repo (e.g. a fixture passed by path)."""
    p = path.resolve()
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def discover_de_file() -> Path | None:
    """Newest date-stamped de/<date>.html, or None. ISO names sort chronologically."""
    if not DE_DIR.exists():
        return None
    cands = sorted(
        (p for p in DE_DIR.iterdir() if DATE_FILE_RE.match(p.name)),
        reverse=True,
    )
    return cands[0] if cands else None


def headwords_from_html(html: str) -> list[str]:
    """Every vocab-item's German headword, lowercased, in document order.

    The headword is the text of the de cell's <strong> with the inline 🔊 <button>
    and any markup stripped, whitespace collapsed, lowercased — that's the ledger's
    canonical key form. Document order is preserved (the brief's teaching order)."""
    out: list[str] = []
    for m in DE_CELL_RE.finditer(html):
        strong_inner = m.group(1)
        # Drop the inline speak button (and anything after it) — the headword is the
        # leading text node only.
        head = BUTTON_SPLIT_RE.split(strong_inner, 1)[0]
        head = TAG_RE.sub("", head)
        head = WS_RE.sub(" ", head).strip().lower()
        if head:
            out.append(head)
    return out


def load_ledger(path: Path) -> dict:
    """Parse the ledger, or start a fresh skeleton if the file doesn't exist yet.
    A present-but-malformed ledger is a hard error — never silently reset it."""
    if not path.exists():
        return {"entries": []}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"{path} is not valid JSON: {exc}")
    if not isinstance(doc, dict) or not isinstance(doc.get("entries"), list):
        die(f"{path} is not a ledger document (missing 'entries' list)")
    return doc


def find_entry(doc: dict, date: str):
    """The single entry for `date`, or None. Also returns its index."""
    for i, e in enumerate(doc["entries"]):
        if isinstance(e, dict) and e.get("date") == date:
            return i, e
    return None, None


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Reconcile the learn-language SRS ledger with the day's DE brief.",
    )
    ap.add_argument("--file", type=Path, default=None,
                    help="canonical DE brief (default: newest public/learn-language/de/<date>.html)")
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER,
                    help=f"ledger JSON (default: {DEFAULT_LEDGER})")
    ap.add_argument("--reviewed", default=None,
                    help="comma-separated DE-canonical (lowercased) review words for this entry")
    ap.add_argument("--theme", default=None, help="theme label for this entry")
    ap.add_argument("--check", action="store_true",
                    help="read-only: exit 1 if the ledger entry would change, don't write")
    ap.add_argument("--pretty", action="store_true", help="indent the JSON summary")
    args = ap.parse_args(argv)

    de_file = args.file or discover_de_file()
    if not de_file or not de_file.exists():
        die(f"DE brief not found: {de_file or '(none in ' + str(DE_DIR) + ')'}")
    m = DATE_FILE_RE.match(de_file.name)
    if not m:
        die(f"DE brief name is not <YYYY-MM-DD>.html: {de_file.name}")
    date = m.group(1)

    try:
        html = de_file.read_text(encoding="utf-8")
    except OSError as exc:
        die(f"cannot read {de_file}: {exc}")

    headwords = headwords_from_html(html)
    if not headwords:
        die(f"no vocab-item headwords found in {de_file} — wrong file or markup changed")

    # Duplicates would corrupt the set/skip logic; surface rather than silently dedup.
    dupes = sorted({h for h in headwords if headwords.count(h) > 1})
    if dupes:
        die(f"duplicate DE headwords in {de_file}: {', '.join(dupes)}")

    doc = load_ledger(args.ledger)
    idx, existing = find_entry(doc, date)

    # reviewed: explicit flag wins; else keep the existing entry's list; else [].
    if args.reviewed is not None:
        reviewed = [w.strip().lower() for w in args.reviewed.split(",") if w.strip()]
    elif existing is not None:
        reviewed = [str(w).strip().lower() for w in (existing.get("reviewed") or [])]
    else:
        reviewed = []

    # reviewed must be a subset of the words actually taught — a review word the brief
    # never showed is a real inconsistency, not something to paper over.
    hw_set = set(headwords)
    stray = [w for w in reviewed if w not in hw_set]
    if stray:
        die(f"reviewed word(s) not among the brief's headwords: {', '.join(stray)}")

    # theme: explicit flag wins; else keep existing; else "".
    if args.theme is not None:
        theme = args.theme
    elif existing is not None:
        theme = existing.get("theme", "")
    else:
        theme = ""

    new_entry = {
        "date": date,
        "theme": theme,
        "headwords": headwords,
        "reviewed": reviewed,
    }

    would_change = existing != new_entry
    n_dupe_dates = sum(1 for e in doc["entries"]
                       if isinstance(e, dict) and e.get("date") == date)

    if args.check:
        summary = {
            "mode": "check",
            "date": date,
            "file": rel(de_file),
            "headwords_in_file": len(headwords),
            "ledger_consistent": (not would_change) and n_dupe_dates == 1,
            "entry_exists": existing is not None,
            "duplicate_dates": n_dupe_dates,
            "would_change": would_change,
        }
        indent = 2 if args.pretty else None
        print(json.dumps(summary, ensure_ascii=False, indent=indent, sort_keys=True))
        return 0 if summary["ledger_consistent"] else 1

    # WRITE: upsert in place (replace same-date entry, never append a duplicate),
    # then keep newest-first and enforce the ~120 cap.
    if idx is not None:
        doc["entries"][idx] = new_entry
        # Defensively drop any *other* entries with the same date (shouldn't exist).
        doc["entries"] = [
            e for i, e in enumerate(doc["entries"])
            if not (i != idx and isinstance(e, dict) and e.get("date") == date)
        ]
        action = "updated"
    else:
        doc["entries"].insert(0, new_entry)
        action = "inserted"

    # Newest-first by date; stable for equal dates.
    doc["entries"].sort(key=lambda e: e.get("date", ""), reverse=True)

    trimmed = 0
    if len(doc["entries"]) > LEDGER_CAP:
        trimmed = len(doc["entries"]) - LEDGER_CAP
        doc["entries"] = doc["entries"][:LEDGER_CAP]

    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    summary = {
        "mode": "write",
        "action": action,
        "date": date,
        "file": rel(de_file),
        "headwords": len(headwords),
        "reviewed": len(reviewed),
        "theme": theme,
        "entries_total": len(doc["entries"]),
        "trimmed_over_cap": trimmed,
    }
    indent = 2 if args.pretty else None
    print(json.dumps(summary, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
