"""Shared helpers for the sports gate modules (football, motorsport).

The recurring sports-brief mistake is a kickoff/session time shown in only one
timezone — the user reads in Brazil (BRT) but follows European competitions
(MEZ/MESZ/CET/CEST) and motorsport in track-local time, so a bare "21:00 MEZ"
with no BRT partner is a real gap.

This is a HEURISTIC and warn-only, so it is tuned to favour PRECISION over
recall: it only flags a time that sits in a clearly schedule-like line and has a
European-zone label but NO Brazil-zone label anywhere in the same block. Loose
narrative mentions of a single time don't get flagged — a noisy gate that fires
on every paragraph would just get ignored, which is worse than a quiet one that
catches the obvious misses.
"""
import re

# Brazil zone labels (the partner that must be present).
BR_ZONE = re.compile(r"\bBR(?:T|ST)\b", re.IGNORECASE)
# European zone labels (German MEZ/MESZ + English CET/CEST).
EU_ZONE = re.compile(r"\b(?:MEZ|MESZ|CES?T)\b")
# A clock time like 21:00 or 9.30.
CLOCK = re.compile(r"\b\d{1,2}[:.]\d{2}\b")


def _block_texts(html: str):
    """Yield the visible text of each block-ish element (li, p, td, h1-h3,
    .tl-events span) — the unit within which a time and its zones should travel
    together. We strip tags so 'two zones in one row but different spans' still
    counts as together."""
    # Grab the inner of common block containers; good enough for a heuristic.
    for m in re.finditer(
        r"<(li|p|td|h1|h2|h3|span)\b[^>]*>(.*?)</\1>", html, re.DOTALL | re.IGNORECASE
    ):
        inner = re.sub(r"<[^>]+>", " ", m.group(2))
        inner = re.sub(r"\s+", " ", inner).strip()
        if inner:
            yield inner


def unpaired_eu_times(html: str, limit: int = 6) -> list[str]:
    """Return up to `limit` block texts that contain a clock time + a European
    zone label but no Brazil zone label — the unpaired-time misses."""
    hits = []
    seen = set()
    for text in _block_texts(html):
        if not CLOCK.search(text):
            continue
        if EU_ZONE.search(text) and not BR_ZONE.search(text):
            key = text[:80]
            if key not in seen:
                seen.add(key)
                hits.append(text[:120])
                if len(hits) >= limit:
                    break
    return hits
