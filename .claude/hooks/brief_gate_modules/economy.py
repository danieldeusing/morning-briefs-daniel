"""Gate module — economy.

BLOCKING: an FX/markets chart driven by fabricated or undated data misleads on
money. When the brief carries a chart data block (e.g. <script id="fx-series">),
this module fails the brief (level="block") if a series looks fabricated:
placeholder/round-number runs, all-identical points, or no date/timestamp
anchoring the series.

No chart data block → nothing to check (not every economy day has a chart), so
this never false-positives on a chartless brief.

Reference implementation of the per-category module interface — see
brief_gate_modules/README.md.
"""
import json
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding  # noqa: E402

# Data blocks that drive FX/market charts. Add ids here if new chart components
# are introduced.
CHART_BLOCK_IDS = ("fx-series", "fx-detail", "benchmark-data")
# A timestamp/date somewhere near the series signals real, sampled data.
DATE_TOKEN_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b|\b\d{1,2}[:.]\d{2}\b")


def _extract_block(html, block_id):
    m = re.search(
        rf'<script\b[^>]*\bid\s*=\s*["\']{re.escape(block_id)}["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


def _numeric_series(obj):
    """Yield (label, list-of-numbers) for any nested {data:[...]} or bare number
    lists found in the parsed JSON — tolerant of the various fx shapes."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "data" and isinstance(v, list) and v and all(
                isinstance(x, (int, float)) for x in v
            ):
                yield ("data", v)
            else:
                yield from _numeric_series(v)
    elif isinstance(obj, list):
        if obj and all(isinstance(x, (int, float)) for x in obj):
            yield ("(list)", obj)
        else:
            for x in obj:
                yield from _numeric_series(x)


def check_brief(ctx):
    out = []
    raw = None
    used_id = None
    for bid in CHART_BLOCK_IDS:
        raw = _extract_block(ctx.html, bid)
        if raw:
            used_id = bid
            break
    if not raw:
        return out  # chartless brief — nothing to validate

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        out.append(Finding("fx-series-unparseable",
                            f"#{used_id} is not valid JSON — the chart will not "
                            "render.", level="block"))
        return out

    series = list(_numeric_series(data))
    if not series:
        out.append(Finding("fx-series-empty",
                            f"#{used_id} carries no numeric data series.",
                            level="block"))
        return out

    for label, nums in series:
        if len(nums) < 2:
            continue
        # Fabrication signature 1: every point identical (flat placeholder).
        if len(set(nums)) == 1:
            out.append(Finding(
                "fx-series-fabricated",
                f"#{used_id} series '{label}' is all identical values "
                f"({nums[0]}) — looks like placeholder, not sampled data.",
                level="block"))
        # Fabrication signature 2: all-zero / all-round placeholder.
        elif all(x == 0 for x in nums):
            out.append(Finding(
                "fx-series-fabricated",
                f"#{used_id} series '{label}' is all zeros — placeholder data.",
                level="block"))

    # Undated: no date or HH:MM token anywhere in the block. Real FX series are
    # anchored to sample dates/times (per § data discipline in the SKILL).
    if not DATE_TOKEN_RE.search(raw):
        out.append(Finding(
            "fx-series-undated",
            f"#{used_id} has no date/timestamp anchoring the data. FX series "
            "must show when they were sampled (labels or a timestamp field).",
            level="block"))

    return out
