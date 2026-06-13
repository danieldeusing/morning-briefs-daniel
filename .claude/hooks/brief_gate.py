#!/usr/bin/env python3
"""Brief-gate — PostToolUse validator for Morning Brief HTML files.

Wired from .claude/settings.json as a PostToolUse hook on Write|Edit. Reads the
hook payload on stdin, and if the edited file is a brief
(public/<category>/<lang>/<YYYY-MM-DD>.html) runs two layers of checks:

  1. SHARED checks (this file) — structural invariants every brief must hold,
     derived from docs/FORMAT.md: <html lang> matches the folder, no leaked
     scaffold comments, balanced <style>/<script> tags, no inline body
     <style>/<script> (except <script type="application/json"> data blocks),
     no orphan <canvas>, a clean </html>, and 4-language structure parity.

  2. PLUGGABLE per-category MODULE — if .claude/hooks/brief_gate_modules/<cat>.py
     exists and defines check_brief(ctx) -> list[Finding], its findings are
     merged in. This is the contract task #58 modules implement; see
     brief_gate_modules/README.md.

Policy: warn-only by default. A check is BLOCKING only if its Finding has
level="block"; blocking findings make the hook emit {"decision":"block",...}
so the agent must fix the file before proceeding. Everything else surfaces as
a non-blocking systemMessage.

Stdlib only. Never raises out of main(): a validator that crashes must not wedge
the agent's Write/Edit, so the top level catches everything and exits 0.
"""
from __future__ import annotations

import json
import re
import sys
import importlib.util
from dataclasses import dataclass, field
from pathlib import Path


# ── Project geometry ───────────────────────────────────────────────────────
HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent              # .claude/hooks → repo root
PUBLIC = REPO_ROOT / "public"
MODULES_DIR = HOOKS_DIR / "brief_gate_modules"

CATEGORIES = {
    "economy", "software", "ai-dev", "ai-usecases", "football",
    "family", "jobs", "learn-language", "motorsport", "stocks-crypto",
}
# Folder name → required <html lang> value (docs/FORMAT.md per-locale table).
LANG_BY_FOLDER = {"de": "de", "en": "en", "pt": "pt-BR", "es": "es-MX"}
ALL_LANGS = ("de", "en", "pt", "es")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.html$")


# ── Finding: the unit shared + category checks both produce ────────────────
@dataclass
class Finding:
    """One check result. level: 'warn' (default, non-blocking) or 'block'.

    check  — short stable id, e.g. "lang-mismatch" or "missing-disclaimer".
    message — human-readable, shown to the agent.
    """
    check: str
    message: str
    level: str = "warn"   # "warn" | "block"

    @property
    def blocking(self) -> bool:
        return self.level == "block"


@dataclass
class BriefContext:
    """Everything a check needs about the brief under edit. Passed to every
    per-category module's check_brief(ctx). Read-only by contract."""
    path: Path                 # absolute path to the edited file
    category: str              # e.g. "economy"
    lang: str                  # folder lang: de|en|pt|es
    date: str                  # YYYY-MM-DD
    html: str                  # full file text
    body: str = field(default="")   # substring from <body ...> onward (or full text)

    def sibling(self, lang: str) -> Path:
        """Path to the same date's file in another language folder."""
        return PUBLIC / self.category / lang / f"{self.date}.html"


# ── Helpers ────────────────────────────────────────────────────────────────
def classify(path: Path):
    """Return (category, lang, date) if path is a brief file, else None."""
    try:
        rel = path.resolve().relative_to(PUBLIC)
    except (ValueError, OSError):
        return None
    parts = rel.parts
    if len(parts) != 3:
        return None
    category, lang, fname = parts
    if category not in CATEGORIES or lang not in LANG_BY_FOLDER:
        return None
    if not DATE_RE.match(fname):
        return None
    return category, lang, fname[:-5]   # strip ".html"


def strip_comments_and_data_blocks(s: str) -> str:
    """Remove HTML comments and <script type=application/json> data blocks, so
    structural scans don't trip over commented-out markup or JSON payloads
    (which legitimately contain < > and 'script' substrings)."""
    s = re.sub(r"<!--.*?-->", "", s, flags=re.DOTALL)
    s = re.sub(
        r'<script\b[^>]*\btype\s*=\s*["\']application/json["\'][^>]*>.*?</script>',
        "", s, flags=re.DOTALL | re.IGNORECASE,
    )
    return s


# ── SHARED checks ──────────────────────────────────────────────────────────
def check_lang(ctx: BriefContext) -> list[Finding]:
    want = LANG_BY_FOLDER[ctx.lang]
    m = re.search(r'<html\b[^>]*\blang\s*=\s*"([^"]*)"', ctx.html, re.IGNORECASE)
    if not m:
        return [Finding("lang-missing", "<html> has no lang attribute "
                        f'(expected lang="{want}").')]
    got = m.group(1)
    if got != want:
        return [Finding("lang-mismatch",
                        f'<html lang="{got}"> in /{ctx.lang}/ folder; '
                        f'expected lang="{want}" per FORMAT.md.')]
    return []


# Scaffold-comment fingerprints from docs/template.html — these must never
# survive into a finished brief (they leak, often in German, into translations).
SCAFFOLD_MARKERS = (
    "BAND 1", "BAND 2", "BODY GRID", "DASHBOARD (per-category",
    "Optional STRIP", "Headline. Fraunces", "Kicker line", "Body class sets",
    "Favicon path is", "Shared styles live", "Optional CDN scripts",
)


def check_scaffold_comments(ctx: BriefContext) -> list[Finding]:
    comments = re.findall(r"<!--(.*?)-->", ctx.html, flags=re.DOTALL)
    hits = []
    for c in comments:
        for marker in SCAFFOLD_MARKERS:
            if marker.lower() in c.lower():
                hits.append(marker)
    if hits:
        uniq = ", ".join(sorted(set(hits)))
        return [Finding("scaffold-comment-leak",
                        f"Template scaffold comment(s) left in output: {uniq}. "
                        "Delete the docs/template.html author comments.")]
    return []


def check_tag_balance(ctx: BriefContext) -> list[Finding]:
    cleaned = strip_comments_and_data_blocks(ctx.html)
    out = []
    for tag in ("style", "script"):
        opens = len(re.findall(rf"<{tag}\b", cleaned, re.IGNORECASE))
        closes = len(re.findall(rf"</{tag}\s*>", cleaned, re.IGNORECASE))
        if opens != closes:
            out.append(Finding(f"unbalanced-{tag}",
                               f"<{tag}> tags unbalanced: {opens} open vs "
                               f"{closes} close."))
    return out


def check_no_inline_body_style_script(ctx: BriefContext) -> list[Finding]:
    """FORMAT.md: no inline <style>/<script> inside <body> — the only allowed
    <script> in body is <script type="application/json"> data blocks."""
    out = []
    if re.search(r"<style\b", ctx.body, re.IGNORECASE):
        out.append(Finding("inline-body-style",
                           "Inline <style> inside <body> is not allowed "
                           "(all CSS lives in lib/styles.css)."))
    # Any body <script> that is NOT type=application/json.
    for m in re.finditer(r"<script\b([^>]*)>", ctx.body, re.IGNORECASE):
        attrs = m.group(1)
        if not re.search(r'type\s*=\s*["\']application/json["\']', attrs, re.IGNORECASE):
            out.append(Finding("inline-body-script",
                               "Inline <script> inside <body> is not allowed "
                               "(only <script type=\"application/json\"> data "
                               "blocks are permitted)."))
            break
    return out


def check_orphan_canvas(ctx: BriefContext) -> list[Finding]:
    """A <canvas> implies a Chart.js component, which needs both a CDN Chart.js
    include and a JSON data block to drive it. A canvas with no JSON data block
    on the page renders empty."""
    if not re.search(r"<canvas\b", ctx.body, re.IGNORECASE):
        return []
    has_json = re.search(
        r'<script\b[^>]*\btype\s*=\s*["\']application/json["\']',
        ctx.html, re.IGNORECASE,
    )
    if not has_json:
        return [Finding("orphan-canvas",
                        "<canvas> present but no <script type=\"application/json\"> "
                        "data block — the chart will render empty.")]
    return []


def check_clean_close(ctx: BriefContext) -> list[Finding]:
    tail = ctx.html.rstrip()[-400:]
    if not re.search(r"</html>\s*$", tail, re.IGNORECASE):
        return [Finding("no-clean-close",
                        "File does not end with a clean </html>. A complete "
                        "standalone document is required (the dashboard iframes it).")]
    if not re.search(r"</body\s*>", ctx.html, re.IGNORECASE):
        return [Finding("no-body-close", "Missing </body>.")]
    return []


def check_lang_parity(ctx: BriefContext) -> list[Finding]:
    """4-language structure parity (warn-only).

    We do NOT warn about merely-missing siblings: the canonical workflow writes
    DE first, then EN/PT/ES in sequence, so a half-present date set is the normal
    mid-authoring state (and the dashboard falls back to DE anyway). Firing on
    every write would be pure noise.

    What we DO flag is structural DRIFT — a non-DE file whose <h2> section count
    differs from the DE canonical, which signals a translation that dropped or
    duplicated a section. That's a real mistake, not in-progress state."""
    out = []
    de_path = ctx.sibling("de")
    if ctx.lang != "de" and de_path.exists():
        try:
            de_html = de_path.read_text(encoding="utf-8")
            de_h2 = len(re.findall(r"<h2\b", de_html, re.IGNORECASE))
            my_h2 = len(re.findall(r"<h2\b", ctx.html, re.IGNORECASE))
            if de_h2 != my_h2:
                out.append(Finding("lang-parity-drift",
                                   f"{ctx.lang} has {my_h2} <h2> vs DE {de_h2} — "
                                   "a translation should mirror the DE structure "
                                   "(dropped or duplicated section?)."))
        except OSError:
            pass
    return out


SHARED_CHECKS = (
    check_lang,
    check_scaffold_comments,
    check_tag_balance,
    check_no_inline_body_style_script,
    check_orphan_canvas,
    check_clean_close,
    check_lang_parity,
)


# ── Per-category module dispatch ───────────────────────────────────────────
def run_category_module(ctx: BriefContext) -> list[Finding]:
    """Load .claude/hooks/brief_gate_modules/<category>.py if present and call
    its check_brief(ctx) -> list[Finding]. The module is optional; a missing or
    broken module never blocks (its failure is surfaced as a warn)."""
    mod_path = MODULES_DIR / f"{ctx.category}.py"
    if not mod_path.exists():
        return []
    try:
        spec = importlib.util.spec_from_file_location(
            f"brief_gate_modules.{ctx.category.replace('-', '_')}", mod_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:  # noqa: BLE001 — a broken module must not wedge edits
        return [Finding("module-load-error",
                        f"Category module {ctx.category}.py failed to load: {e}")]
    fn = getattr(module, "check_brief", None)
    if not callable(fn):
        return [Finding("module-no-entrypoint",
                        f"{ctx.category}.py has no check_brief(ctx) function.")]
    try:
        results = fn(ctx) or []
    except Exception as e:  # noqa: BLE001
        return [Finding("module-runtime-error",
                        f"{ctx.category}.py check_brief raised: {e}")]
    # Defensive: coerce what the module returned into OUR Finding class. We
    # duck-type rather than isinstance — when brief_gate.py runs as __main__
    # (the hook subprocess), a module's `from brief_gate import Finding` loads a
    # SECOND copy of this module, so its Finding is a different class object and
    # isinstance() would silently drop every finding. Match by attributes.
    clean = []
    for r in results:
        if hasattr(r, "check") and hasattr(r, "message"):
            clean.append(Finding(r.check, r.message, getattr(r, "level", "warn")))
        elif isinstance(r, dict) and "check" in r and "message" in r:
            clean.append(Finding(r["check"], r["message"], r.get("level", "warn")))
    return clean


# ── Orchestration ──────────────────────────────────────────────────────────
def validate(path: Path) -> list[Finding]:
    info = classify(path)
    if not info:
        return []
    category, lang, date = info
    try:
        html = path.read_text(encoding="utf-8")
    except OSError:
        return []
    body_start = html.lower().find("<body")
    body = html[body_start:] if body_start != -1 else html
    ctx = BriefContext(path=path, category=category, lang=lang, date=date,
                       html=html, body=body)
    findings: list[Finding] = []
    for check in SHARED_CHECKS:
        try:
            findings.extend(check(ctx) or [])
        except Exception as e:  # noqa: BLE001
            findings.append(Finding("shared-check-error",
                                    f"{check.__name__} raised: {e}"))
    findings.extend(run_category_module(ctx))
    return findings


def emit(findings: list[Finding], path: Path) -> None:
    """Print the hook JSON. Blocking findings → decision:block; otherwise a
    non-blocking systemMessage. Silent when clean."""
    if not findings:
        return
    label = path.name
    try:
        label = str(path.resolve().relative_to(REPO_ROOT))
    except (ValueError, OSError):
        pass
    blocking = [f for f in findings if f.blocking]
    warns = [f for f in findings if not f.blocking]

    lines = []
    if blocking:
        lines.append(f"brief-gate BLOCK — {label}")
        for f in blocking:
            lines.append(f"  ✗ [{f.check}] {f.message}")
    if warns:
        lines.append(f"brief-gate warnings — {label}")
        for f in warns:
            lines.append(f"  • [{f.check}] {f.message}")
    text = "\n".join(lines)

    out = {}
    if blocking:
        out["decision"] = "block"
        out["reason"] = text
    else:
        out["systemMessage"] = text
    print(json.dumps(out))


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return 0
    tool_input = payload.get("tool_input") or {}
    fp = tool_input.get("file_path") or payload.get("file_path")
    if not fp:
        return 0
    findings = validate(Path(fp))
    emit(findings, Path(fp))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — never wedge the agent on a validator bug
        sys.exit(0)
