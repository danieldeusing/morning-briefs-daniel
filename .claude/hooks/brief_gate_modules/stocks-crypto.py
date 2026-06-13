"""Gate module — stocks-crypto. Language-aware.

BLOCKING: a stocks/crypto brief that ships without a clear "not investment
advice" disclaimer is a liability problem — fails the brief (level="block") when
no disclaimer phrase is found, in any of the four languages.

WARN: the brief's remit is five asset buckets — Magnificent-7/big-tech, oil
(Brent + WTI), gold (XAU), majors (BTC + ETH), and the speculative tail
(memecoins / gaming / AI tokens). If a bucket is entirely absent the day's
coverage has a hole; we warn (not block — a quiet day in one bucket is fine, but
a missing bucket is usually an omission worth a look).

Reference implementation of the per-category module interface — see
brief_gate_modules/README.md.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402


# Per-language disclaimer fingerprints. A brief passes if ANY variant for its
# language appears (case-insensitive). Keyed off ctx.lang so the EN/PT/ES files
# aren't judged against the German phrase.
DISCLAIMER_PATTERNS = {
    "de": [r"keine\s+anlageberatung", r"keine\s+finanzberatung",
           r"stellt\s+keine\s+(anlage|finanz)beratung"],
    "en": [r"not\s+(financial|investment)\s+advice",
           r"no\s+(financial|investment)\s+advice"],
    "pt": [r"não\s+é\s+(uma\s+)?(recomenda|consultoria|aconselhamento)",
           r"não\s+constitui\s+(recomenda|consultoria)"],
    "es": [r"no\s+es\s+(asesor|asesoramiento|recomendaci)",
           r"no\s+constituye\s+(asesor|recomendaci)"],
}

# Five coverage buckets. Patterns lean on proper nouns (language-agnostic) plus
# per-language common-noun variants for gold, so the EN/PT/ES files match too.
COVERAGE_BUCKETS = {
    "Mag-7 / big-tech":
        r"Mag(nificent)?[\s-]?7|Nvidia|Apple|Microsoft|Alphabet|Amazon|Meta|Tesla|Broadcom",
    "oil (Brent + WTI)": r"\bBrent\b|\bWTI\b",
    "gold (XAU)": r"\bXAU\b|\bGold\b|\bouro\b|\boro\b",
    "majors (BTC + ETH)": r"\bBTC\b|\bETH\b|Bitcoin|Ethereum",
    "speculative tail (meme/gaming/AI)":
        r"memecoin|meme-coin|\bDOGE\b|\bSHIB\b|\bPEPE\b|gaming|\bAI[\s-]?(coin|token)",
}


def check_brief(ctx):
    out = []
    text = ctx.html

    # 1) Disclaimer — BLOCK.
    patterns = DISCLAIMER_PATTERNS.get(ctx.lang, [])
    if not any(re.search(p, text, re.IGNORECASE) for p in patterns):
        out.append(Finding(
            "missing-disclaimer",
            f"No investment-advice disclaimer found for lang={ctx.lang}. "
            "A stocks-crypto brief must carry a clear 'not investment advice' "
            "line (e.g. DE 'Keine Anlageberatung', EN 'Not financial advice').",
            level="block",
        ))

    # 2) Coverage buckets — WARN per missing bucket.
    missing = [name for name, pat in COVERAGE_BUCKETS.items()
               if not re.search(pat, text, re.IGNORECASE)]
    if missing:
        out.append(Finding(
            "coverage-bucket-missing",
            f"No coverage of: {', '.join(missing)}. The brief's five buckets are "
            "Mag-7/big-tech, oil (Brent+WTI), gold (XAU), majors (BTC+ETH), and "
            "the speculative tail (meme/gaming/AI) — a missing bucket is usually "
            "an omission.",
            level="warn",
        ))
    return out
