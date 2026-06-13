#!/usr/bin/env python3
"""sports-time-trizone — render one event time in the three zones the football
and motorsport briefs require, with DST computed (never guessed).

Daniel reads in Ribeirão Claro/PR — BRT, UTC-3, and Brazil has NO daylight
saving, so BRT is -3 year-round. The competitions he follows run in Europe
(MEZ/CET = UTC+1 winter, MESZ/CEST = UTC+2 summer) and, for motorsport, at a
track that can sit in any zone on earth. The recurring brief mistake is a bare
"21:00 MEZ" with no Brazil partner, or a hand-computed offset that's an hour off
because someone forgot which side of a DST switch the date falls on.

This script removes the arithmetic. You give it a wall-clock time, the date, and
the zone that time is stated in; it converts to the others via the real IANA tz
database (stdlib `zoneinfo`), so the summer/winter offset for that exact date is
correct by construction. Brazil never shifts; Europe shifts on the EU schedule;
the track zone shifts on its own local schedule — all handled for you.

Two briefs, two house formats (both produced):
  • football  — two zones:  "MEZ + BRT", e.g. "21:00 MEZ / 16:00 BRT"
  • motorsport — three zones: "track-local + BRT + MESZ",
                 e.g. "16:00 EDT / 17:00 BRT / 22:00 CEST"
The script prints both orderings plus a JSON object, so the routine can paste
the string it needs and the gate's dual-zone check passes.

CLI:
    trizone.py --time 21:00 --date 2026-05-23 --in-zone Europe/Berlin
    trizone.py --time 16:00 --date 2026-05-23 --in-zone America/New_York \
               --track-zone America/New_York        # motorsport: name the venue zone

--in-zone is the zone the --time is given in. --track-zone (motorsport only)
names the venue zone if it differs from --in-zone; omit it for football. Zones
are IANA names ("Europe/Berlin", "America/Sao_Paulo", "Asia/Bahrain") or one of
the convenience aliases below.

Stdlib only. Exit 0 on success, 2 on a bad argument (unknown zone, malformed
time/date) — the routine should treat exit 2 as "fix the inputs", never as
licence to hand-write a time.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Daniel's home zone — the partner that must always be present. Brazil has no
# DST, so this is UTC-3 every day of the year.
BRT = "America/Sao_Paulo"
# Europe reference zone for the football/motorsport briefs. Berlin gives the
# MEZ (winter, UTC+1) / MESZ (summer, UTC+2) split the briefs use; the label is
# derived from the actual offset on the date, so we never mislabel the season.
EUROPE = "Europe/Berlin"

# Convenience aliases so a routine can say "berlin" or "brt" instead of the full
# IANA string. Track zones for common motorsport venues are included so the F1
# calendar is one short token, not an IANA lookup each time.
ALIASES = {
    "brt": BRT, "saopaulo": BRT, "brasilia": BRT, "ribeiraoclaro": BRT,
    "berlin": EUROPE, "europe": EUROPE, "cet": EUROPE, "cest": EUROPE,
    "mez": EUROPE, "mesz": EUROPE,
    "uk": "Europe/London", "london": "Europe/London",
    "et": "America/New_York", "edt": "America/New_York", "est": "America/New_York",
    "miami": "America/New_York", "montreal": "America/New_York",
    "austin": "America/Chicago", "cot": "America/Chicago",
    "lasvegas": "America/Los_Angeles", "pt": "America/Los_Angeles",
    "bahrain": "Asia/Bahrain", "qatar": "Asia/Qatar", "abudhabi": "Asia/Dubai",
    "jeddah": "Asia/Riyadh", "saudi": "Asia/Riyadh",
    "suzuka": "Asia/Tokyo", "japan": "Asia/Tokyo", "tokyo": "Asia/Tokyo",
    "singapore": "Asia/Singapore", "shanghai": "Asia/Shanghai", "china": "Asia/Shanghai",
    "melbourne": "Australia/Melbourne", "australia": "Australia/Melbourne",
    "interlagos": BRT, "brazil": BRT, "saopaulogp": BRT,
    "mexico": "America/Mexico_City", "mexicocity": "America/Mexico_City",
    "imola": EUROPE, "monza": EUROPE, "spa": EUROPE, "zandvoort": EUROPE,
    "barcelona": EUROPE, "montmelo": EUROPE, "redbullring": EUROPE, "spielberg": EUROPE,
    "hungaroring": "Europe/Budapest", "budapest": "Europe/Budapest",
    "silverstone": "Europe/London",
}

# Map a real UTC offset (hours) to the label the briefs use for the European
# zone, so "MEZ" vs "MESZ" is decided by the date's offset, not by guesswork.
EUROPE_LABEL = {1: "MEZ", 2: "MESZ"}
# English/CET labels the briefs also accept (motorsport uses CEST/CET).
EUROPE_LABEL_EN = {1: "CET", 2: "CEST"}


def resolve_zone(token: str) -> ZoneInfo:
    """Accept an IANA name or a convenience alias; raise SystemExit(2) on an
    unknown zone so the caller fixes the input instead of getting a wrong time."""
    key = token.strip().lower().replace("/", "").replace("_", "").replace(" ", "")
    name = ALIASES.get(key, token.strip())
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        sys.exit(_err(f"unknown timezone {token!r} (use an IANA name like "
                      "'Europe/Berlin' or an alias like 'berlin'/'brt')"))


def _err(msg: str) -> int:
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    return 2


def _fmt(dt: datetime) -> str:
    """24h HH:MM, zero-padded — the brief's clock format."""
    return dt.strftime("%H:%M")


def _europe_label(dt_eu: datetime, english: bool = False) -> str:
    off_h = int(dt_eu.utcoffset().total_seconds() // 3600)
    table = EUROPE_LABEL_EN if english else EUROPE_LABEL
    return table.get(off_h, dt_eu.tzname() or f"UTC{off_h:+d}")


def convert(time_str: str, date_str: str, in_zone: str, track_zone: str | None):
    src = resolve_zone(in_zone)
    try:
        naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        sys.exit(_err(f"bad --time/--date: expected HH:MM and YYYY-MM-DD, "
                      f"got {time_str!r} / {date_str!r}"))
    aware = naive.replace(tzinfo=src)

    brt = aware.astimezone(ZoneInfo(BRT))
    eu = aware.astimezone(ZoneInfo(EUROPE))
    eu_lbl = _europe_label(eu)            # MEZ / MESZ
    eu_lbl_en = _europe_label(eu, english=True)  # CET / CEST

    result = {
        "ok": True,
        "input": {"time": time_str, "date": date_str, "in_zone": str(src)},
        "brt": {"time": _fmt(brt), "label": "BRT"},
        "europe": {"time": _fmt(eu), "label": eu_lbl, "label_en": eu_lbl_en},
        # football: two zones, MEZ + BRT, in the brief's canonical order.
        "football_string": f"{_fmt(eu)} {eu_lbl} / {_fmt(brt)} BRT",
    }

    # Motorsport: three zones. The track zone is the venue; if the caller didn't
    # name one we treat the in-zone as the track (e.g. a European round given in
    # Berlin time is its own track zone).
    track = resolve_zone(track_zone) if track_zone else src
    trk = aware.astimezone(track)
    trk_lbl = trk.tzname() or str(track)
    result["track"] = {"time": _fmt(trk), "zone": str(track), "label": trk_lbl}
    # track-local + BRT + MESZ (motorsport house order).
    result["motorsport_string"] = (
        f"{_fmt(trk)} {trk_lbl} / {_fmt(brt)} BRT / {_fmt(eu)} {eu_lbl_en}"
    )
    return result


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="trizone.py",
        description="Convert one event time into BRT + Europe (+ track) zones "
                    "with DST computed from the real tz database.")
    ap.add_argument("--time", required=True, help="wall-clock time, HH:MM (24h)")
    ap.add_argument("--date", required=True, help="date the event falls on, YYYY-MM-DD")
    ap.add_argument("--in-zone", required=True,
                    help="the zone --time is given in (IANA name or alias)")
    ap.add_argument("--track-zone", default=None,
                    help="motorsport venue zone if different from --in-zone")
    args = ap.parse_args(argv)
    result = convert(args.time, args.date, args.in_zone, args.track_zone)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
