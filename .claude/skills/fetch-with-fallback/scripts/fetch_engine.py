#!/usr/bin/env python3
"""fetch-with-fallback — resilient single-value fetch over a source ladder.

The daily newsletter routines pull live numbers (FX rates, a dengue count from a
gov PDF, a SWE-Bench score, a league standing). Those fetches fail in predictable
ways: a 403, a PDF where you expected HTML, an empty JS shell that only renders
client-side, a layout change that breaks your selector. When that happens the
honest move is to try the NEXT trustworthy source — not to invent a number.

This engine does exactly that. You hand it an ordered LADDER of sources; it tries
each in turn, and on any failure (network error, wrong content type, empty/JS
shell, or a parse miss) it steps down to the next rung. It returns the first
success as {value, source_url, source_name, date, rung, ...} — or, if every rung
fails, a structured result listing why each one failed, so the routine can decide
to omit the figure rather than fabricate it.

Design choices that matter:
  • The DATE travels with the value. A number with no sample date is suspect (the
    economy brief-gate blocks undated fx-series). If a source exposes a date we
    capture it; otherwise we mark date_inferred=true and date=today so the caller
    knows it wasn't sourced.
  • pdftotext is used only as a fallback for PDF rungs, and only if present. No
    hard dependency — a missing pdftotext just fails that rung and steps down.
  • Stdlib only (urllib). No third-party HTTP client, so it runs anywhere the
    routines run.

CLI:
    python fetch_engine.py <ladder.json>          # one metric, ladder = list of rungs
    python fetch_engine.py <config.json> --key X   # config = {"X": [rungs], ...}; fetch X
Prints the result dict as JSON. Exit 0 if a value was found, 3 if all rungs failed.

A rung (one source) looks like:
    {
      "name": "ECB daily reference rate",
      "url": "https://www.ecb.europa.eu/.../eurofxref-daily.xml",
      "kind": "json" | "html" | "pdf",
      "extract": <see below>,          # how to pull the value
      "date_extract": <optional>,      # how to pull the sample date
      "headers": {"User-Agent": "..."} # optional per-rung headers
    }

extract / date_extract by kind:
    json : {"path": "rates.BRL"}        dot/bracket path into parsed JSON
    html : {"regex": "id=\"eurbrl\">([0-9.,]+)"}   first capture group
    pdf  : {"regex": "Casos: ([0-9.]+)"}           regex over pdftotext output
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date


DEFAULT_UA = "Mozilla/5.0 (compatible; MorningBriefFetch/1.0)"
TIMEOUT = 20


class RungError(Exception):
    """A single rung failed; message explains why (used to build the report)."""


# ── Fetch ──────────────────────────────────────────────────────────────────
def _http_get(url: str, headers: dict | None) -> tuple[bytes, str]:
    """Return (body_bytes, content_type). Raises RungError on any network/HTTP
    failure (incl. 403) so the ladder steps down."""
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            return body, ctype
    except urllib.error.HTTPError as e:
        raise RungError(f"HTTP {e.code} {e.reason}")
    except urllib.error.URLError as e:
        raise RungError(f"network error: {e.reason}")
    except Exception as e:  # noqa: BLE001 — timeouts, malformed URLs, etc.
        raise RungError(f"fetch failed: {e}")


def _looks_like_js_shell(text: str) -> bool:
    """Heuristic: a near-empty HTML body whose visible text is tiny but that ships
    a big script bundle is almost certainly client-rendered — our regex will find
    nothing useful. Flag it so the report says 'JS-rendered' instead of a vague
    parse miss."""
    stripped = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    stripped = re.sub(r"<[^>]+>", "", stripped)
    visible = stripped.strip()
    has_root_div = re.search(r'<div\s+id=["\'](root|app|__next)["\']', text, re.IGNORECASE)
    return len(visible) < 200 and bool(has_root_div)


# ── Extraction ─────────────────────────────────────────────────────────────
def _json_path(obj, path: str):
    """Walk a dot/bracket path: 'rates.BRL', 'data[0].score'. Raises RungError on
    a miss so the ladder steps down rather than the routine getting None."""
    cur = obj
    for token in re.findall(r"[^.\[\]]+", path):
        if isinstance(cur, list):
            try:
                cur = cur[int(token)]
            except (ValueError, IndexError):
                raise RungError(f"json path miss at [{token}]")
        elif isinstance(cur, dict):
            if token not in cur:
                raise RungError(f"json path miss at '{token}'")
            cur = cur[token]
        else:
            raise RungError(f"json path miss: cannot descend into {type(cur).__name__}")
    return cur


def _regex_first(text: str, pattern: str) -> str:
    m = re.search(pattern, text)
    if not m:
        raise RungError(f"regex miss: /{pattern}/")
    return (m.group(1) if m.groups() else m.group(0)).strip()


def _pdf_to_text(body: bytes) -> str:
    if not shutil.which("pdftotext"):
        raise RungError("pdftotext not available for PDF rung")
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", "-", "-"], input=body,
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise RungError(f"pdftotext failed: {e}")
    if proc.returncode != 0:
        raise RungError(f"pdftotext exit {proc.returncode}")
    return proc.stdout.decode("utf-8", "replace")


def _extract(kind: str, body: bytes, ctype: str, spec: dict) -> str:
    if kind == "json":
        # Tolerate a JSON served as text/html; only fail if it truly won't parse.
        try:
            obj = json.loads(body.decode("utf-8", "replace"))
        except (json.JSONDecodeError, ValueError):
            raise RungError("response is not valid JSON")
        return str(_json_path(obj, spec["path"]))
    if kind == "html":
        if b"%PDF-" in body[:8]:
            raise RungError("expected HTML, got a PDF")
        text = body.decode("utf-8", "replace")
        if _looks_like_js_shell(text):
            raise RungError("page is a JS shell (client-rendered) — no static value")
        return _regex_first(text, spec["regex"])
    if kind == "pdf":
        text = _pdf_to_text(body)
        return _regex_first(text, spec["regex"])
    raise RungError(f"unknown rung kind '{kind}'")


# ── Ladder ─────────────────────────────────────────────────────────────────
def fetch_metric(ladder: list[dict]) -> dict:
    """Try each rung in order; return the first success or a failure report."""
    attempts = []
    for i, rung in enumerate(ladder):
        name = rung.get("name", rung.get("url", f"rung {i}"))
        try:
            kind = rung.get("kind", "html")
            body, ctype = _http_get(rung["url"], rung.get("headers"))
            value = _extract(kind, body, ctype, rung["extract"])
            result = {
                "ok": True,
                "value": value,
                "source_url": rung["url"],
                "source_name": name,
                "rung": i,
            }
            # Date: prefer a sourced date; otherwise mark inferred so the caller
            # knows it wasn't pulled from the source (gate-relevant).
            if rung.get("date_extract"):
                try:
                    result["date"] = _extract(kind, body, ctype, rung["date_extract"])
                    result["date_inferred"] = False
                except RungError:
                    result["date"] = date.today().isoformat()
                    result["date_inferred"] = True
            else:
                result["date"] = date.today().isoformat()
                result["date_inferred"] = True
            return result
        except RungError as e:
            attempts.append({"rung": i, "name": name, "url": rung.get("url"),
                             "error": str(e)})
        except KeyError as e:
            attempts.append({"rung": i, "name": name,
                             "error": f"malformed rung: missing {e}"})
    return {"ok": False, "value": None, "attempts": attempts}


def main(argv: list[str]) -> int:
    if not argv:
        print(json.dumps({"ok": False, "error": "usage: fetch_engine.py "
                          "<ladder-or-config.json> [--key METRIC]"}))
        return 2
    cfg_path = argv[0]
    key = None
    if "--key" in argv:
        key = argv[argv.index("--key") + 1]
    try:
        with open(cfg_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": f"cannot load config: {e}"}))
        return 2
    if key is not None:
        if not isinstance(data, dict) or key not in data:
            print(json.dumps({"ok": False, "error": f"metric '{key}' not in config"}))
            return 2
        ladder = data[key]
    else:
        ladder = data
    if not isinstance(ladder, list):
        print(json.dumps({"ok": False, "error": "ladder must be a list of rungs "
                          "(or pass --key for a multi-metric config)"}))
        return 2
    result = fetch_metric(ladder)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
