"""Gate module — motorsport. Warn-only.

Checks (heuristic, non-blocking):
  • a session/event time in a European zone (MESZ/CEST) with no BRT partner in
    the same block — the same dual-timezone discipline as football, shared via
    _sport.unpaired_eu_times. (The brief's convention is track-local + BRT +
    MESZ; the three zones often split across sentences, so we only flag the
    clearest miss — a EU-zone time with no Brazil partner nearby — to stay
    quiet enough to be useful.)
  • drivers' AND constructors' standings should both be present — F1 weekends
    carry two tables. We check there are at least two <table>s; an incomplete
    standings section (one or none) warns.

Language note: zone labels (BRT/MESZ) and standings are kept across languages,
so these checks are lang-agnostic.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _sport  # noqa: E402


def check_brief(ctx):
    out = []

    for line in _sport.unpaired_eu_times(ctx.html):
        out.append(Finding("time-unpaired",
                           f"Session time in a European zone without a BRT "
                           f"partner: “{line}”. Show track-local + BRT + MESZ.",
                           level="warn"))

    # Standings: F1 carries drivers' + constructors'. Count tables loosely.
    n_tables = len(re.findall(r"<table\b", ctx.html, re.IGNORECASE))
    if n_tables < 2:
        out.append(Finding("standings-incomplete",
                           f"Only {n_tables} <table> present; F1 standings "
                           "usually need both drivers' and constructors' tables.",
                           level="warn"))
    return out
