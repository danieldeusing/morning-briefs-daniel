"""Gate module — software. Warn-only.

The software brief writes each story as a full section headed by a single <h2>
(per FORMAT.md — there's no intermediate "Top-Stories" tier, and stories are not
stacked under bare <h3> heads). The shared brief-gate checks already cover the
structural HTML; this module adds one software-specific smell:

  • a body-grid column with MULTIPLE bare <h3> story-heads and NO <h2> — i.e.
    stories stacked under <h3> instead of each getting its own <h2> section.
    (Today's briefs use one <h2> per story and zero bare <h3>, so this is
    quiet by default; it catches a regression toward the old pattern.)

A CVE-without-source check was considered but the shared sourcing convention +
the section-level footnotes already cover it, so we don't duplicate it here —
keeping this module minimal per the gate's "don't add noise" principle.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402


def check_brief(ctx):
    m = re.search(r'<div class="body-grid', ctx.body)
    if not m:
        return []
    grid = ctx.body[m.start():]
    # Split into columns and look for a column with ≥2 <h3> and 0 <h2>.
    cols = re.split(r'<div class="col">', grid)
    out = []
    for i, col in enumerate(cols[1:], 1):
        # stop the column at the next col boundary (already split) — col is the
        # text up to the next "<div class=\"col\">".
        h2 = len(re.findall(r"<h2\b", col, re.IGNORECASE))
        h3 = len(re.findall(r"<h3\b", col, re.IGNORECASE))
        if h2 == 0 and h3 >= 2:
            out.append(Finding(
                "h3-stacked-stories",
                f"body-grid column {i} has {h3} bare <h3> heads and no <h2> — "
                "each story should be its own <h2> section, not stacked under "
                "<h3>.", level="warn"))
    return out
