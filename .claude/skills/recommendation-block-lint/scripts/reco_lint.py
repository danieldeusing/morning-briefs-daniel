#!/usr/bin/env python3
"""recommendation-block-lint — check the stocks-crypto brief's recommendation
blocks carry all five mandated fields, in any of the four languages.

The stocks-crypto SKILL makes every recommendation a five-part contract — it is
Daniel's decision basis for real money, so a recommendation that's missing the
timeframe, or the counter-scenario, or the dated price evidence is materially
incomplete, not just terse. The five fields (per the routine's
`Empfehlungs-Format (PFLICHT)`):

  1. Verdict       — BUY / SELL / HOLD, carried as a <span class="chip">.
  2. Why           — detailed reasoning (fundamentals, catalysts, macro, ELI5).
  3. Timeframe     — concrete *when*, tied to a dated event to wait for.
  4. Forecast      — target range + probability + a counter-scenario.
  5. Price evidence — real, DATED numbers (24h/7d/30d moves, levels).

In the HTML, each recommendation is an `<h3>…Empfehlung…</h3>` immediately
followed by a `<div class="callout info">…</div>`. This linter finds each such
block and checks for the five fields by their visible label, matched per
language (the labels translate; the markup does not).

It is a LINT — every finding is advisory (warn). It is the SAME spirit as the
stocks-crypto brief-gate module (which BLOCKS only on the missing disclaimer);
recommendation completeness is important but not liability-blocking, so this runs
as a checklist you act on, not a gate. Run it after writing the recommendations,
before you call the brief done.

CLI:
    reco_lint.py <brief.html> [<brief.html> ...]
Prints a per-file report and a JSON summary. Exit 0 if every recommendation in
every file carries all five fields; 1 if any field is missing (so a routine can
branch on it).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# A recommendation block: an <h3> whose text marks it as a recommendation,
# followed (allowing whitespace) by a <div class="callout info">…</div>. The
# heading word is per-language; the callout class is invariant.
RECO_HEADING = {
    "de": r"Empfehlung",
    "en": r"Recommendation|Call",          # the brief uses "Call — NVDA" as the reco heading
    "pt": r"Recomenda(ç|c)(ã|a)o",
    "es": r"Recomendaci(ó|o)n",
}

# Field fingerprints per language. Each field passes if ANY of its variants is
# present in the block's text (case-insensitive). We match the LABEL the brief
# uses ("Verdict:", "Warum:", …) plus a couple of natural synonyms, so a brief
# that phrases the label slightly differently still passes.
FIELD_PATTERNS = {
    "verdict": {
        "de": [r"\bVerdict\b", r"\bEinschätzung\b", r"\bFazit\b"],
        "en": [r"\bVerdict\b", r"\bCall\b", r"\bBottom line\b"],
        "pt": [r"\bVeredito\b", r"\bVerdict\b", r"\bConclus(ã|a)o\b"],
        "es": [r"\bVeredicto\b", r"\bVerdict\b", r"\bConclusi(ó|o)n\b"],
    },
    "why": {
        "de": [r"\bWarum\b", r"\bBegründung\b", r"\bGrund\b"],
        "en": [r"\bWhy\b", r"\bRationale\b", r"\bReason(ing)?\b"],
        # "Por quê" / "por que" / "porquê" — the accented ê breaks a trailing \b,
        # so match the stem and an optional accented vowel without a word boundary.
        "pt": [r"\bpor\s*qu[êe]", r"\bporqu[êe]", r"\bRaz(ã|a)o\b", r"\bMotivo\b", r"\bJustificativa\b"],
        "es": [r"\bpor\s*qu[ée]", r"\bporqu[ée]", r"\bRaz(ó|o)n\b", r"\bMotivo\b", r"\bJustificaci(ó|o)n\b"],
    },
    "timeframe": {
        "de": [r"\bTimeframe\b", r"\bZeithorizont\b", r"\bZeitrahmen\b", r"\bHorizont\b"],
        "en": [r"\bTimeframe\b", r"\bTime\s*frame\b", r"\bHorizon\b", r"\bWhen\b"],
        "pt": [r"\bPrazo\b", r"\bHorizonte\b", r"\bTimeframe\b", r"\bQuando\b"],
        "es": [r"\bPlazo\b", r"\bHorizonte\b", r"\bTimeframe\b", r"\bCu(á|a)ndo\b"],
    },
    "forecast": {
        "de": [r"\bPrognose\b", r"\bZielspanne\b", r"\bKursziel\b", r"\bAusblick\b"],
        "en": [r"\bForecast\b", r"\bTarget\b", r"\bOutlook\b", r"\bPrice target\b"],
        "pt": [r"\bPrevis(ã|a)o\b", r"\bProje(ç|c)(ã|a)o\b", r"\bAlvo\b", r"\bPerspectiva\b"],
        "es": [r"\bPron(ó|o)stico\b", r"\bProyecci(ó|o)n\b", r"\bObjetivo\b", r"\bPerspectiva\b"],
    },
}

# A price-shaped token: $1.23, US$77.071, R$5,03, €1.16, 4.67%, "−6 %".
PRICE_TOKEN = re.compile(
    r"(?:US\$|R\$|\$|€|£)\s?\d[\d.,]*"      # a currency amount
    r"|[-+−]?\d[\d.,]*\s?%"                  # or a percentage
)
# A date/period token anchoring the timeframe to a dated event: an ISO date, a
# DD.MM, a month name, or a relative period (24h/7d/30d/Q2/H2).
DATE_TOKEN = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{1,2}\.\d{1,2}\.?(?:\d{2,4})?\b"
    r"|\b\d{1,3}\s?(?:h|d|w|m|months?|days?|weeks?|tagen?|wochen?|monate?n?)\b"
    r"|\bQ[1-4]\b|\bH[12]\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
    r"|Mär|Mai|Okt|Dez|jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez"
    r"|ene|abr|ago|dic)\w*\b",
    re.IGNORECASE,
)

CHIP_RE = re.compile(r'<span\b[^>]*\bclass\s*=\s*"[^"]*\bchip\b[^"]*"[^>]*>(.*?)</span>',
                     re.DOTALL | re.IGNORECASE)


def detect_lang(html: str, path: Path) -> str:
    """Folder name wins (…/stocks-crypto/<lang>/file.html); else <html lang>."""
    parts = path.resolve().parts
    for p in reversed(parts):
        if p in ("de", "en", "pt", "es"):
            return p
    m = re.search(r'<html\b[^>]*\blang\s*=\s*"([a-z]{2})', html, re.IGNORECASE)
    return m.group(1).lower() if m else "de"


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def find_reco_blocks(html: str, lang: str):
    """Yield (heading_text, block_html) for each recommendation. The block is the
    <div class="callout info"> that follows the <h3>…recommendation…</h3>."""
    heading_word = RECO_HEADING.get(lang, RECO_HEADING["de"])
    h3_re = re.compile(
        rf'<h3\b[^>]*>(?P<title>(?:(?!</h3>).)*?{heading_word}(?:(?!</h3>).)*?)</h3>'
        r'\s*(?P<block><div\b[^>]*\bclass\s*=\s*"[^"]*\bcallout\b[^"]*\binfo\b[^"]*"[^>]*>)',
        re.DOTALL | re.IGNORECASE,
    )
    for m in h3_re.finditer(html):
        # Walk <div>/</div> from the opening callout to its matching close so a
        # nested <div> inside the callout doesn't truncate the block.
        start = m.end("block")
        depth = 1
        for tag in re.finditer(r"<(/?)div\b", html[start:], re.IGNORECASE):
            if tag.group(1):
                depth -= 1
                if depth == 0:
                    block = html[start:start + tag.start()]
                    yield strip_tags(m.group("title")), block
                    break
            else:
                depth += 1


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def lint_block(block_html: str, lang: str) -> list[str]:
    """Return the list of MISSING field ids for one recommendation block."""
    text = strip_tags(block_html)
    missing = []

    # Verdict: a label OR a BUY/SELL/HOLD chip is enough (the brief carries the
    # verdict as a chip, sometimes without a separate "Verdict:" label).
    verdict_label = _has_any(text, FIELD_PATTERNS["verdict"].get(lang, []))
    chips = " ".join(strip_tags(c) for c in CHIP_RE.findall(block_html))
    verdict_chip = bool(re.search(
        r"\b(BUY|SELL|HOLD|HALTEN|KAUF|VERKAUF|AKKUMULIEREN|MEIDEN|COMPRAR|VENDER|"
        r"MANTER|MANTENER|REDUZIR|REDUCIR|ÜBERGEWICHT|UNTERGEWICHT|UNDERWEIGHT|"
        r"OVERWEIGHT|BEOBACHTEN|WATCH|OBSERVAR|SPEKULATIV|ESPECULATIVO)\b",
        chips, re.IGNORECASE))
    if not (verdict_label or verdict_chip):
        missing.append("verdict (BUY/SELL/HOLD chip or label)")

    if not _has_any(text, FIELD_PATTERNS["why"].get(lang, [])):
        missing.append("why (detailed reasoning)")

    # Timeframe: needs the label AND a dated/period anchor (a timeframe with no
    # date is the most common soft miss the routine wants flagged).
    tf_label = _has_any(text, FIELD_PATTERNS["timeframe"].get(lang, []))
    tf_date = bool(DATE_TOKEN.search(text))
    if not tf_label:
        missing.append("timeframe (label)")
    elif not tf_date:
        missing.append("timeframe is present but has no dated event/period "
                       "(add the date or horizon to wait for)")

    # Forecast: label AND at least one price/percent token (a target range needs
    # a number) AND a counter-scenario cue.
    fc_label = _has_any(text, FIELD_PATTERNS["forecast"].get(lang, []))
    fc_num = bool(PRICE_TOKEN.search(text))
    # A counter-scenario can be phrased many ways in the brief. The house style
    # is often a Bull/Bear/Base tier set (each with a probability), but it can
    # also be a conditional ("ohne X weiter abwärts", "if Y then Z"), a named
    # downside/risk, or an explicit "Gegen-Szenario". Match any of these so a
    # genuine downside framing isn't flagged as missing — over-narrow cues here
    # produce false positives that erode trust in the lint.
    COUNTER_TIERS = r"\b(Bull|Bear|Base|Basis|Upside|Downside)\b"
    counter_cues = {
        "de": [COUNTER_TIERS, r"\bGegen-?Szenario\b", r"\bRisiko\b", r"\bandernfalls\b",
               r"\bfalls\b", r"\bsonst\b", r"\bohne\b", r"\bwenn\b", r"\bbricht\b", r"\bdroht\b"],
        "en": [COUNTER_TIERS, r"\bcounter-?scenario\b", r"\brisk\b", r"\bif\b",
               r"\botherwise\b", r"\bunless\b", r"\bbreaks?\b", r"\bthreat"],
        "pt": [COUNTER_TIERS, r"\bcen(á|a)rio\s+contr(á|a)rio\b", r"\brisco\b", r"\bse\b",
               r"\bcaso\b", r"\bsem\b", r"\bquebra"],
        "es": [COUNTER_TIERS, r"\bescenario\s+contrario\b", r"\briesgo\b", r"\bsi\b",
               r"\bde lo contrario\b", r"\bsin\b", r"\brompe"],
    }
    fc_counter = _has_any(text, counter_cues.get(lang, []))
    if not fc_label:
        missing.append("forecast (label)")
    else:
        if not fc_num:
            missing.append("forecast has no target number (add a price/% range)")
        if not fc_counter:
            missing.append("forecast has no counter-scenario (add the 'else/if' case)")

    # Price evidence: the field demands real, DATED numbers. What matters is the
    # SUBSTANCE — a price/percent figure plus a date anchor. We do NOT nag about a
    # missing "Beleg:"/"Preço:" label when the dated numbers are plainly there;
    # the label varies by translation and a label-only complaint is noise that
    # erodes trust in the lint. Flag only genuinely-absent substance.
    pe_num = bool(PRICE_TOKEN.search(text))
    pe_date = bool(DATE_TOKEN.search(text))
    if not pe_num:
        missing.append("price evidence: no real price/% figure in the block")
    elif not pe_date:
        missing.append("price evidence: figures present but undated "
                       "(add the 24h/7d/30d or a sample date)")

    return missing


def lint_file(path: Path) -> dict:
    try:
        html = path.read_text(encoding="utf-8")
    except OSError as e:
        return {"path": str(path), "error": str(e), "blocks": []}
    lang = detect_lang(html, path)
    blocks = []
    for title, block_html in find_reco_blocks(html, lang):
        missing = lint_block(block_html, lang)
        blocks.append({"title": title, "missing": missing, "ok": not missing})
    return {"path": str(path), "lang": lang, "blocks": blocks,
            "n_blocks": len(blocks),
            "n_incomplete": sum(1 for b in blocks if b["missing"])}


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: reco_lint.py <brief.html> [<brief.html> ...]", file=sys.stderr)
        return 2
    reports = [lint_file(Path(a)) for a in argv]
    any_missing = False
    for rep in reports:
        print(f"\n■ {rep['path']}")
        if rep.get("error"):
            print(f"  ! cannot read: {rep['error']}")
            continue
        if rep["n_blocks"] == 0:
            print(f"  (no recommendation blocks found — lang={rep.get('lang')})")
            continue
        print(f"  lang={rep['lang']}  {rep['n_blocks']} recommendation(s), "
              f"{rep['n_incomplete']} incomplete")
        for b in rep["blocks"]:
            if b["missing"]:
                any_missing = True
                print(f"  ✗ {b['title']}")
                for m in b["missing"]:
                    print(f"      – {m}")
            else:
                print(f"  ✓ {b['title']}")
    print("\n" + json.dumps({"files": reports, "all_complete": not any_missing},
                            ensure_ascii=False))
    return 1 if any_missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
