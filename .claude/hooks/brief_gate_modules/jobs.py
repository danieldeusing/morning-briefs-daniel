"""Gate module — jobs.

The jobs board renders from an inline <script id="jobs-listings"> JSON payload
(see the jobs-board component). This module validates that payload's schema so a
malformed listing set can't ship.

Checks:
  • BLOCK if #jobs-listings is present but not valid JSON, or has no listings —
    the board would render empty / broken.
  • WARN on per-listing schema gaps: missing id/title/url, fit_score not an int
    in 0–100, role_type not in {freelance, employee, intriguing}, or a url that
    isn't https. (Warn, not block — a few soft gaps shouldn't stop a publish,
    but they should be visible.)
  • WARN on a stray "$" in a salary_range that isn't a genuine USD figure — the
    brief is BRL/EUR-denominated; a bare "$" is usually a templating slip. Real
    "US$" / "USD" comp is allowlisted.
  • WARN if a non-DE file's #jobs-listings block isn't byte-identical to the DE
    sibling's. The payload is language-neutral by contract — one source of truth,
    embedded verbatim in all four files (listing title/company/url/fit_reason/tags
    stay canonical; only the board chrome in lib/newsletter.js is translated). So
    a divergence means a run accidentally translated a listing field or let the
    four blocks drift out of sync — silently breaking the single-source guarantee.
    A strict compare can't false-positive on a correct run, since there's no
    per-language text in the block.

No-op when there's no #jobs-listings block (e.g. an older jobs file).
"""
import json
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402

VALID_ROLE_TYPES = {"freelance", "employee", "intriguing"}

LISTINGS_RE = re.compile(
    r'<script\b[^>]*\bid="jobs-listings"[^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _extract_listings_block(html):
    """Return the raw inner text of the #jobs-listings <script>, or None."""
    m = LISTINGS_RE.search(html)
    return m.group(1) if m else None


def _check_cross_lang_identity(ctx, block):
    """WARN if this file's #jobs-listings differs from the DE sibling's.

    Runs only for non-DE files (DE is the reference; comparing it to itself is
    pointless and would double-report). No-op when there's no DE sibling or it
    carries no block. Whitespace is preserved in the compare on purpose — the
    block is emitted verbatim in all four files, so any byte difference is a real
    divergence, not formatting noise."""
    if ctx.lang == "de":
        return []
    de_path = ctx.sibling("de")
    if not de_path.exists():
        return []   # nothing to compare against (DE not written yet)
    try:
        de_block = _extract_listings_block(de_path.read_text(encoding="utf-8"))
    except OSError:
        return []
    if de_block is None or de_block == block:
        return []
    return [Finding(
        "jobs-listings-lang-drift",
        f"#jobs-listings in the {ctx.lang} file differs from the DE sibling — the "
        "payload must be byte-identical across all 4 languages (single source of "
        "truth; listing fields stay canonical, only chrome is translated). Re-embed "
        "the exact DE block.",
        level="warn")]


def check_brief(ctx):
    block = _extract_listings_block(ctx.html)
    if block is None:
        return []   # no listings payload on this file

    out = []
    out.extend(_check_cross_lang_identity(ctx, block))
    try:
        data = json.loads(block)
    except (json.JSONDecodeError, ValueError) as e:
        out.append(Finding("jobs-json-unparseable",
                           f"#jobs-listings is not valid JSON ({e}) — the board "
                           "will not render.", level="block"))
        return out

    listings = data.get("listings") if isinstance(data, dict) else None
    if not isinstance(listings, list) or not listings:
        out.append(Finding("jobs-no-listings",
                           "#jobs-listings has no 'listings' array — the board "
                           "renders empty.", level="block"))
        return out

    gaps = []
    for idx, job in enumerate(listings):
        jid = job.get("id") or f"#{idx}"
        if not job.get("id"):
            gaps.append(f"{jid}: missing id (persistence key)")
        if not job.get("title"):
            gaps.append(f"{jid}: missing title")
        url = str(job.get("url", ""))
        if not url:
            gaps.append(f"{jid}: missing url")
        elif not url.startswith("https"):
            gaps.append(f"{jid}: url not https ({url[:40]})")
        fit = job.get("fit_score")
        if not isinstance(fit, int) or not 0 <= fit <= 100:
            gaps.append(f"{jid}: fit_score not int 0–100 ({fit!r})")
        rt = job.get("role_type")
        if rt not in VALID_ROLE_TYPES:
            gaps.append(f"{jid}: role_type {rt!r} not in {sorted(VALID_ROLE_TYPES)}")
        # Stray $ in salary (allow genuine USD comp).
        sal = str(job.get("salary_range", ""))
        if "$" in sal and not re.search(r"US\$|USD", sal):
            gaps.append(f"{jid}: bare '$' in salary_range '{sal}' "
                        "(BRL/EUR brief — genuine USD comp should say US$/USD)")

    if gaps:
        shown = "; ".join(gaps[:8]) + (" …" if len(gaps) > 8 else "")
        out.append(Finding("jobs-schema-gaps",
                           f"{len(gaps)} listing schema issue(s): {shown}",
                           level="warn"))
    return out
