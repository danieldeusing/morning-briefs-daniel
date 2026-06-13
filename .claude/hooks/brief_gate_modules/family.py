"""Gate module — family. Warn-only. Language-aware.

Check: a health figure (dengue / SRAG / RSV / gripe / InfoGripe count) must be
anchored to an epidemiological-week stamp so the reader knows which week it
covers — InfoGripe/SES data is always reported per SE (semana epidemiológica).
The brief stamps these as "SE NN/YYYY" or "nº NN".

Heuristic, tuned for precision: we only warn when the brief clearly presents
health data (a health keyword appears alongside a number) but carries NO epi-week
stamp ANYWHERE in the file. That catches the real "forgot to date the health
figures" miss without firing per-paragraph. Health keywords are matched per
language so the EN/PT/ES files aren't judged against German terms.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402

# Per-language health-topic keywords. dengue/SRAG/RSV are proper-ish and shared.
HEALTH_TERMS = {
    "de": r"dengue|SRAG|RSV|grippe|gripe|InfoGripe|atemwegs",
    "en": r"dengue|SRAG|RSV|flu|influenza|InfoGripe|respiratory",
    "pt": r"dengue|SRAG|VSR|gripe|influenza|InfoGripe|respirat[óo]ri",
    "es": r"dengue|SRAG|VSR|gripe|influenza|InfoGripe|respiratori",
}
# Epi-week stamp, per-language abbreviations: DE/PT/ES "SE NN/YYYY" (semana
# epidemiológica), EN "EW NN/YYYY" (epidemiological week), or a "nº NN" bulletin
# number. The brief translates the abbreviation, so accept all variants.
EPI_STAMP = re.compile(
    r"\b(?:SE|EW|MMWR)\s*\d{1,2}(?:[–-]\d{1,2})?/\d{4}\b"
    r"|\b(?:semana\s+epidemiol[óo]gica|epidemiological\s+week)\s*\d{1,2}\b"
    r"|\bn\.?[º°]\s*\d{1,3}\b",
    re.IGNORECASE,
)
NUMBER = re.compile(r"\b\d[\d.,]*\b")


def check_brief(ctx):
    terms = HEALTH_TERMS.get(ctx.lang, HEALTH_TERMS["de"])
    body = ctx.body
    has_health = re.search(terms, body, re.IGNORECASE) and NUMBER.search(body)
    if not has_health:
        return []   # no health data presented → nothing to anchor
    if EPI_STAMP.search(body):
        return []   # health data is dated somewhere → good
    return [Finding(
        "health-undated",
        "Health figures (dengue/SRAG/RSV/gripe) are present but no "
        "epidemiological-week stamp (\"SE NN/YYYY\" or \"nº NN\") appears in the "
        "file — date the data so the reader knows the reporting week.",
        level="warn",
    )]
