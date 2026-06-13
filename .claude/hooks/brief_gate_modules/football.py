"""Gate module — football. Warn-only.

Checks (heuristic, non-blocking):
  • a kickoff/event time shown in a European zone (MEZ/MESZ/CET) with no BRT
    partner in the same block — the dual-timezone rule (Daniel reads in Brazil,
    follows the Bundesliga/EL in European time). Via _sport.unpaired_eu_times.
  • each <table class="standings-table"> should carry a 9-COLUMN header whose
    first column is the rank ("#"), and 18 (Bundesliga) or 20 (Brasileirão)
    body rows. A truncated table or a dropped column is a real content miss.

Language note: the column LABELS translate (DE Sp/S/U/N/Tore/TD/Pkt → EN
P/W/D/L/Goals/GD/Pts → PT J/V/E/D/Gols/SG/Pts → ES PJ/G/E/P/Goles/DG/Pts), so we
check the column COUNT and the rank-column marker, NOT the German label text —
checking exact German labels would false-positive on every translated file. The
time labels (BRT/MEZ) are kept across languages, so the time check is lang-safe.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _sport  # noqa: E402

EXPECTED_COLS = 9
VALID_ROWCOUNTS = {18, 20}


def _tables(html):
    return re.findall(r'<table class="standings-table"[^>]*>(.*?)</table>', html,
                      re.DOTALL | re.IGNORECASE)


def check_brief(ctx):
    out = []

    # 1) Unpaired European times.
    for line in _sport.unpaired_eu_times(ctx.html):
        out.append(Finding("time-unpaired",
                           f"Time in a European zone without a BRT partner: "
                           f"“{line}”. Show BRT + MEZ together.",
                           level="warn"))

    # 2) Standings tables.
    tables = _tables(ctx.html)
    if not tables:
        out.append(Finding("standings-missing",
                           "No <table class=\"standings-table\"> found — the "
                           "Bundesliga + Brasileirão tables are expected.",
                           level="warn"))
    for i, t in enumerate(tables):
        ths = [re.sub(r"<[^>]+>", "", x).strip()
               for x in re.findall(r"<th[^>]*>(.*?)</th>", t, re.DOTALL | re.IGNORECASE)]
        rows = len(re.findall(r"<tr", t, re.IGNORECASE)) - 1  # minus header
        # Validate column COUNT + rank-column marker, not language-specific labels.
        if ths and len(ths) != EXPECTED_COLS:
            out.append(Finding("standings-cols",
                               f"standings-table #{i} has {len(ths)} columns "
                               f"({ths}); expected {EXPECTED_COLS} "
                               "(#, club, played, W, D, L, goals, GD, points).",
                               level="warn"))
        elif ths and ths[0] != "#":
            out.append(Finding("standings-header",
                               f"standings-table #{i} first column is '{ths[0]}', "
                               "expected the rank column '#'.", level="warn"))
        if rows not in VALID_ROWCOUNTS:
            out.append(Finding("standings-rows",
                               f"standings-table #{i} has {rows} body rows; "
                               "expected 18 (Bundesliga) or 20 (Brasileirão).",
                               level="warn"))
    return out
