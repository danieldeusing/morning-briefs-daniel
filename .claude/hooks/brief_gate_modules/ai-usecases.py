"""Gate module — ai-usecases. Warn-only.

Check: the closing twiceD project-ideas block (`.idee` cards) must be sourced —
each idea is a market-grounded suggestion, so the block should carry at least
one `.src` citation or footnote reference. An unsourced ideas block reads as
made-up rather than researched.

Heuristic, tuned for precision: we only warn when `.idee` cards are present but
the whole twiceD-ideen container (or the cards within it) carries NO `.src`,
`.footnotes`, or `[N]`-style footnote ref. We don't require one per card — the
research often cites shared sources — just flag a wholly unsourced block.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402


def check_brief(ctx):
    if not re.search(r'class="idee"', ctx.html, re.IGNORECASE):
        return []   # no ideas block on this page

    # Look at the twiceD-ideen container if present, else the whole body.
    m = re.search(r'class="twiced-ideen"(.*)$', ctx.html, re.DOTALL | re.IGNORECASE)
    region = m.group(1) if m else ctx.body

    has_source = (
        re.search(r'class="src"', region, re.IGNORECASE)
        or re.search(r'class="footnote', region, re.IGNORECASE)
        or re.search(r'class="h2-refs"', region, re.IGNORECASE)
        or re.search(r'href="https?://', region, re.IGNORECASE)
    )
    if not has_source:
        return [Finding(
            "idee-unsourced",
            "twiceD project-idea (.idee) cards are present but the block carries "
            "no source/footnote — ground the ideas with at least one citation.",
            level="warn",
        )]
    return []
