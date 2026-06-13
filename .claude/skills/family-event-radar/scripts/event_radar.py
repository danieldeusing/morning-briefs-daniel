#!/usr/bin/env python3
"""family-event-radar — the deterministic half of the family event sweep.

Two subcommands, mirroring the deterministic/model split that jobs-prefs-apply
uses: this script does the parts that are pure arithmetic / IO and would only
drift if re-derived in prose each morning. It deliberately does NOT parse event
text out of pages — that's the model's job (see SKILL.md "The boundary").

  sweep   Fetch every source page in sources/family-events.json, ring by ring
          (near->far), and print each source's RING + DISTANCE + URL + the
          fetched page text. The model reads these blocks and pulls out the
          actual events. Fetch failures (403, PDF-where-HTML, JS shell, network)
          are reported per source and skipped — never fabricated, never fatal.

  filter  THE GUARD. Read a JSON list of event dicts the model assembled
          (each at least {"date": "YYYY-MM-DD", "ring": "<ring>", ...}), drop
          anything dated before TODAY, and sort the survivors by (ring_order,
          date). This is the "reject the stale February Londrina page and the
          past-dated SESC event" check, done in code so it can't be forgotten.
          Today is read from the system clock, never hardcoded.

Stdlib only. Reuses the fetch primitives from the sibling fetch-with-fallback
skill so there's one fetch implementation, not two.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# Reuse the fetch primitives from the fetch-with-fallback skill — one fetch
# implementation, not two. The skills sit side by side under .claude/skills/.
_FWF = Path(__file__).resolve().parents[2] / "fetch-with-fallback" / "scripts"
sys.path.insert(0, str(_FWF))
try:
    from fetch_engine import (  # noqa: E402
        _http_get, _looks_like_js_shell, _pdf_to_text, RungError,
    )
    _HAVE_ENGINE = True
except Exception:  # noqa: BLE001 — degrade gracefully if the sibling moved
    _HAVE_ENGINE = False

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "sources" / "family-events.json"
# Cap per-source text so a sweep of ~14 pages stays a sane size for the model to
# read. Event listings live near the top of these pages; 20k chars is plenty.
MAX_CHARS = 20_000


# ── sweep ────────────────────────────────────────────────────────────────────
def _fetch_page(url: str, kind: str) -> tuple[str | None, str | None]:
    """Return (text, None) on success or (None, reason) on failure. Mirrors the
    ladder's failure modes (403 / wrong-type / JS shell) so a dud source is
    skipped with a reason, not silently empty and not fabricated."""
    if not _HAVE_ENGINE:
        return None, "fetch-with-fallback engine not importable"
    try:
        body, _ctype = _http_get(url, None)
    except RungError as e:
        return None, str(e)
    if kind == "pdf":
        try:
            return _pdf_to_text(body)[:MAX_CHARS], None
        except RungError as e:
            return None, str(e)
    # html
    if b"%PDF-" in body[:8]:
        return None, "expected HTML, got a PDF (set kind=pdf for this source)"
    text = body.decode("utf-8", "replace")
    if _looks_like_js_shell(text):
        return None, "page is a JS shell (client-rendered) — open it manually"
    return text[:MAX_CHARS], None


def cmd_sweep(config_path: Path) -> int:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    rings = sorted(cfg["rings"], key=lambda r: r["ring_order"])
    today = date.today().isoformat()
    out_blocks = []
    ok_count = 0
    fail_count = 0
    for ring in rings:
        for src in ring["sources"]:
            text, reason = _fetch_page(src["url"], src.get("kind", "html"))
            block = {
                "ring": ring["ring"],
                "ring_order": ring["ring_order"],
                "distance": ring["distance"],
                "ring_label": ring["label"],
                "source_name": src["name"],
                "source_url": src["url"],
            }
            if text is not None:
                block["ok"] = True
                block["text"] = text
                ok_count += 1
            else:
                block["ok"] = False
                block["error"] = reason
                fail_count += 1
            out_blocks.append(block)
    print(json.dumps({
        "today": today,
        "instructions": (
            "Read each ok block's 'text' and extract family/kid events. For every "
            "event keep {date:'YYYY-MM-DD', ring, distance, was, eignung, preis, "
            "quelle:source_url}. Then pipe your assembled list through "
            "`event_radar.py filter` to drop past-dated events and rank by ring. "
            "Do NOT invent events for sources whose ok=false — open them by hand "
            "or omit them."
        ),
        "ok": ok_count,
        "failed": fail_count,
        "sources": out_blocks,
    }, ensure_ascii=False, indent=2))
    return 0


# ── filter (the guard) ───────────────────────────────────────────────────────
def _ring_order_map(config_path: Path) -> dict[str, int]:
    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        return {r["ring"]: r["ring_order"] for r in cfg["rings"]}
    except Exception:  # noqa: BLE001 — filter must work even without the config
        return {"kern": 0, "day-trip": 1, "londrina": 2, "sp-range": 3}


def filter_events(events: list[dict], today: str, ring_order: dict[str, int]) -> dict:
    """Drop events dated before `today`; sort survivors by (ring_order, date).

    Returns kept + dropped (with reasons) so nothing vanishes silently — a
    dropped event is visible, just not in the brief. Events with an unparseable
    or missing date are kept but flagged (undated), because silently dropping a
    real event is worse than surfacing one the model must date by hand. An
    unknown ring sorts last (order 99) and is flagged."""
    kept, dropped, flagged = [], [], []
    for ev in events:
        d = str(ev.get("date", "")).strip()
        ro = ring_order.get(ev.get("ring", ""), 99)
        ev = {**ev, "_ring_order": ro}
        if ev.get("ring", "") not in ring_order:
            ev["_warning"] = f"unknown ring '{ev.get('ring')}' — sorts last"
            flagged.append(ev)
        # Date in YYYY-MM-DD compares correctly as a plain string.
        if len(d) == 10 and d[4] == "-" and d[7] == "-":
            if d < today:
                dropped.append({**ev, "_reason": f"past-dated ({d} < {today})"})
            else:
                kept.append(ev)
        else:
            ev["_warning"] = f"unparseable date '{d}' — kept, date it by hand"
            kept.append(ev)
            flagged.append(ev)
    kept.sort(key=lambda e: (e["_ring_order"], str(e.get("date", "9999-99-99"))))
    return {
        "today": today,
        "kept": kept,
        "dropped": dropped,
        "flagged": flagged,
        "kept_count": len(kept),
        "dropped_count": len(dropped),
    }


def cmd_filter(events_path: Path | None, config_path: Path, today_override: str | None) -> int:
    raw = (events_path.read_text(encoding="utf-8") if events_path
           else sys.stdin.read())
    try:
        events = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"error": f"input is not valid JSON: {e}"}))
        return 2
    if isinstance(events, dict) and "events" in events:
        events = events["events"]
    if not isinstance(events, list):
        print(json.dumps({"error": "expected a JSON list of event objects"}))
        return 2
    today = today_override or date.today().isoformat()
    result = filter_events(events, today, _ring_order_map(config_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="family event radar — sweep + date/ring filter")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("sweep", help="fetch all source pages, near->far")
    sp.add_argument("--config", type=Path, default=DEFAULT_CONFIG)

    fp = sub.add_parser("filter", help="drop past-dated events, rank by ring")
    fp.add_argument("--events", type=Path, default=None,
                    help="JSON file of event dicts (default: stdin)")
    fp.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    fp.add_argument("--today", default=None,
                    help="override today (YYYY-MM-DD) — for fixtures/tests only")

    args = ap.parse_args(argv)
    if args.cmd == "sweep":
        return cmd_sweep(args.config)
    if args.cmd == "filter":
        return cmd_filter(args.events, args.config, args.today)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
