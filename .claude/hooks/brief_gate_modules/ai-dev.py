"""Gate module — ai-dev. Warn-only.

Check: when the brief carries a benchmark chart (a <script ... id="bench-data">
block), the benchmark numbers must be sourced — a cited source URL and a date
should appear in the file so a reader can verify the leaderboard figures.
No-op when there's no bench chart (most days don't have one), so it never
false-positives on a chartless brief.

Heuristic, tuned for precision: we only require that SOME http(s) source link and
SOME date token exist in the file when a bench-data block is present. We don't
try to bind a specific URL to the chart — that's a judgment call — just flag the
clear miss of an unsourced benchmark.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402

DATE_TOKEN = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b|\b\d{1,2}\.\d{1,2}\.20\d{2}\b"
                        r"|\b\d{1,2}/\d{1,2}/20\d{2}\b")


def check_brief(ctx):
    has_bench = re.search(r'id="bench-data"', ctx.html, re.IGNORECASE)
    if not has_bench:
        return []   # no benchmark chart → nothing to source

    out = []
    has_link = re.search(r'href="https?://', ctx.html, re.IGNORECASE)
    has_date = DATE_TOKEN.search(ctx.body)
    if not has_link:
        out.append(Finding("bench-unsourced",
                           "A #bench-data benchmark chart is present but no "
                           "source link (href=\"http…\") appears in the file — "
                           "cite where the leaderboard numbers come from.",
                           level="warn"))
    if not has_date:
        out.append(Finding("bench-undated",
                           "A #bench-data benchmark chart is present but no date "
                           "appears in the file — benchmark scores move; show "
                           "when they were captured.", level="warn"))
    return out
