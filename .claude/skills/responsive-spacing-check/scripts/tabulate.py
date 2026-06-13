#!/usr/bin/env python3
"""responsive-spacing-check — format collected measurements into a review table.

Input: a JSON array of measurement results from measure.js — one object per
(breakpoint × category) you probed. Read from a file arg or stdin:

    python3 tabulate.py results.json
    cat results.json | python3 tabulate.py

Each result needs at least: url/port, innerW, selector, matched, overflowX, rows[]
(each row: w, h, fontSizePx, marginTop, gapToPrev). measure.js produces exactly
this shape.

Output: a fixed-width table (one line per probe) plus a FLAGS section that calls
out the things worth a human's eye:
  • horizontal overflow (overflowX > 0) — the mobile-break failure class
  • font-size inconsistency — the matched elements don't all share a size at a
    given width (the timeline-vs-bullets #30 case)
  • a probe that matched 0 elements — selector typo or wrong page
  • verification on the wrong port — anything not :8090 (stale-lib trap; the
    port-guard hook warns live, this flags it in the report too)

This is a REPORT, not a gate — it surfaces metrics for a judgment call, since
"right amount of spacing" is taste. It just makes the numbers legible across
breakpoints and categories so you're not eyeballing one page at a time.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict


def load(argv):
    src = open(argv[0], encoding="utf-8") if argv else sys.stdin
    with src as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return data


def short_url(u: str) -> str:
    # …/economy/de/2026-05-20.html → economy/de
    try:
        parts = u.split("//", 1)[1].split("/")
        # drop host, keep category/lang
        segs = [p for p in parts[1:] if p and not p.endswith(".html")]
        return "/".join(segs[:2]) or u
    except (IndexError, AttributeError):
        return u


def main(argv) -> int:
    try:
        results = load(argv)
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read measurements: {e}", file=sys.stderr)
        return 2
    if not results:
        print("no measurements provided.")
        return 0

    # ── Table ──
    hdr = f"{'page':<16} {'width':>6} {'match':>5} {'ovf':>5} {'gap(min/max)':>14} {'font(set)':>16}"
    print(hdr)
    print("-" * len(hdr))
    flags = []
    for r in results:
        page = short_url(r.get("url", "?"))
        width = r.get("innerW", "?")
        matched = r.get("matched", 0)
        ovf = r.get("overflowX", 0)
        rows = r.get("rows", [])
        gaps = [row["gapToPrev"] for row in rows if row.get("gapToPrev") is not None]
        gap_str = f"{min(gaps)}/{max(gaps)}" if gaps else "-"
        fonts = sorted({row["fontSizePx"] for row in rows if "fontSizePx" in row})
        font_str = ",".join(str(f) for f in fonts) if fonts else "-"
        print(f"{page:<16} {width:>6} {matched:>5} {ovf:>5} {gap_str:>14} {font_str:>16}")

        # Flags
        label = f"{page}@{width}"
        if ovf and ovf > 0:
            flags.append(f"OVERFLOW  {label}: page overflows horizontally by {ovf}px "
                         "(content wider than viewport).")
        if matched == 0:
            flags.append(f"NO-MATCH  {label}: selector matched 0 elements "
                         "(selector typo, or wrong page for this component?).")
        if len(fonts) > 1:
            flags.append(f"FONT-MIX  {label}: matched elements have differing "
                         f"font-sizes {fonts} — intentional, or inconsistent?")
        port = str(r.get("port", ""))
        if port and port != "8090":
            flags.append(f"PORT      {label}: measured on :{port}, not :8090 — "
                         "if a lib edit is uncommitted you may be seeing a STALE "
                         "lib. Re-measure on :8090.")

    # ── Cross-page gap consistency (same selector, compare gaps across pages at
    # the same width) ──
    by_width = defaultdict(list)
    for r in results:
        gaps = [row["gapToPrev"] for row in r.get("rows", []) if row.get("gapToPrev") is not None]
        if gaps:
            by_width[r.get("innerW")].append((short_url(r.get("url", "?")), min(gaps), max(gaps)))
    for width, entries in by_width.items():
        allgaps = [g for _, lo, hi in entries for g in (lo, hi)]
        if len(entries) > 1 and allgaps and (max(allgaps) - min(allgaps)) > 8:
            detail = ", ".join(f"{p}:{lo}-{hi}" for p, lo, hi in entries)
            flags.append(f"GAP-DRIFT @{width}: inter-element gap varies across "
                         f"categories ({detail}) — a shared-lib rule should give "
                         "the same gap everywhere.")

    print()
    if flags:
        print("FLAGS:")
        for f in flags:
            print(f"  ⚑ {f}")
    else:
        print("FLAGS: none — gaps consistent, no overflow, single font per set, all on :8090.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
