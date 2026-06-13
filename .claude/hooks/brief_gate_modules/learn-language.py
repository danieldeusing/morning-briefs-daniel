"""Gate module — learn-language. Warn-only.

The vocab data (words in DE/EN/PT/ES + which are reviews) is language-neutral:
the SAME word set, with the SAME items flagged as spaced-repetition reviews,
should appear in all four per-language files — only the surrounding chrome
translates. So the structural counts must match across the four siblings.

Checks (warn-only):
  • vocab-row parity — the four files must have the same number of vocab rows.
    A mismatch means a translation dropped or added a word (the cells aren't the
    parallel set they should be).
  • review-chip parity — the four files must flag the same number of review
    items. A mismatch (e.g. de=1, en=5) means the review marking drifted between
    languages — the review chips don't agree.

The review chip is correctly TRANSLATED per file ("WIEDERHOLUNG" in DE, "REVIEW"
in EN, "REVISÃO" in PT, "REPASO" in ES), so we count it against the file's own
language label, NOT a single literal "REVIEW" token — counting the English word
everywhere would score the correctly-translated DE/PT/ES chips as zero and fire a
bogus mismatch (the original bug this module had).

We compare counts across siblings rather than byte-diffing cell text, because
the cell *content* legitimately differs per file in surrounding markup; the
counts are the robust, low-false-positive signal for "the parallel structure
broke". The check runs once per file (it reads all four siblings each time);
identical counts everywhere → silent.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402

LANGS = ("de", "en", "pt", "es")

# The review chip's visible label per language. A vocab item is "review-flagged"
# when it carries a chip with this word. We accept any of the four labels in any
# file (a translation occasionally leaves a sibling's word in), so the count is
# robust to that — what we care about is HOW MANY review chips, not which word.
REVIEW_LABELS = ("WIEDERHOLUNG", "REVIEW", "REVISÃO", "REVISAO", "REPASO")
REVIEW_CHIP_RE = re.compile(
    r">\s*(?:" + "|".join(REVIEW_LABELS) + r")\s*<", re.IGNORECASE,
)


def _counts(html):
    return {
        "vocab_rows": len(re.findall(r'class="vocab-row"', html)),
        "review_chips": len(REVIEW_CHIP_RE.findall(html)),
    }


def check_brief(ctx):
    # Gather counts for every sibling that exists.
    per_lang = {}
    for lang in LANGS:
        p = ctx.sibling(lang)
        if not p.exists():
            continue
        try:
            per_lang[lang] = _counts(p.read_text(encoding="utf-8"))
        except OSError:
            continue
    if len(per_lang) < 2:
        return []   # nothing to compare yet (mid-authoring)

    out = []
    for metric, label in (("vocab_rows", "vocab rows"),
                           ("review_chips", "review chips")):
        values = {lang: c[metric] for lang, c in per_lang.items()}
        distinct = set(values.values())
        if len(distinct) > 1:
            detail = ", ".join(f"{lang}={values[lang]}" for lang in sorted(values))
            out.append(Finding(
                f"langparity-{metric.replace('_', '-')}",
                f"{label} differ across languages ({detail}) — the vocab set and "
                "its review flags should be identical in all four files.",
                level="warn",
            ))
    return out
