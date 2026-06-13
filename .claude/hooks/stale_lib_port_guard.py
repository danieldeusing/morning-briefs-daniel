#!/usr/bin/env python3
"""stale-lib port-guard — PreToolUse warning for preview verification on a
stale-lib port.

Background (the trap this kills): for verification, public/ is served on :8090 by
the local no-cache server (`tools/serve_local.py`, start it on demand — it
replaced the old Caddy/Docker edge). It sends `Cache-Control: no-cache` on /lib/*,
so lib edits load fresh. The Claude Preview default server on :8765 sends NO cache
headers, so the browser reuses a STALE lib/styles.css|newsletter.js. Verifying a
lib change against :8765 silently tests the OLD lib — producing false "it works" /
"it's broken" calls. (This cost ~6 eval round-trips in the jobs-board / spacing
work.)

This hook fires on preview / browser navigation tool calls. If the tool input
references a non-:8090 localhost target (typically :8765) WHILE a public/lib/*
file is uncommitted in git, it emits a non-blocking warning telling the agent to
verify on :8090 instead. Warn-only — never blocks; the agent may still use :8765
deliberately (e.g. to check cached behaviour).

Stdlib only. Always exits 0 (a guard bug must never wedge a tool call).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent

FRESH_PORT = "8090"          # tools/serve_local.py — no-cache on /lib/*
# Any localhost authority with a port that ISN'T 8090. Matches host:port in URLs
# anywhere in the tool input (preview_eval's `expression`, navigate's `url`, …).
LOCALHOST_RE = re.compile(
    r"(?:https?://)?(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?::(\d+))?", re.IGNORECASE
)


def lib_is_dirty() -> list[str]:
    """Return the list of uncommitted public/lib/* paths (staged, unstaged, or
    untracked). Empty if lib is clean or git is unavailable."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--", "public/lib"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    dirty = []
    for line in out.stdout.splitlines():
        # porcelain: "XY path" — strip the 2-char status + space.
        path = line[3:].strip() if len(line) > 3 else ""
        if path:
            dirty.append(path)
    return dirty


def stale_targets(blob: str) -> list[str]:
    """Find localhost targets in the tool input that are NOT the fresh :8090
    port. A bare localhost with no port is ambiguous → ignored (the default
    Python server is explicit about :8765)."""
    bad = []
    for m in LOCALHOST_RE.finditer(blob):
        port = m.group(1)
        if port and port != FRESH_PORT:
            bad.append(m.group(0))
    return bad


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_input = payload.get("tool_input") or {}
    # Scan the whole tool input as text — covers preview_eval `expression`,
    # navigate `url`, browser_batch nested actions, etc., without coupling to
    # one tool's arg shape.
    try:
        blob = json.dumps(tool_input, ensure_ascii=False)
    except (TypeError, ValueError):
        blob = str(tool_input)

    targets = stale_targets(blob)
    if not targets:
        return 0
    dirty = lib_is_dirty()
    if not dirty:
        return 0  # navigating to :8765 is fine when lib is committed/clean

    uniq = sorted(set(targets))
    dirty_str = ", ".join(dirty[:6]) + (" …" if len(dirty) > 6 else "")
    msg = (
        "stale-lib port-guard: this preview/navigation targets "
        f"{uniq} while lib changes are uncommitted ({dirty_str}). "
        f":8765 serves /lib/* WITHOUT no-cache, so you may be verifying against "
        f"a STALE lib. Use http://localhost:{FRESH_PORT}/ instead (start it with "
        "`python3 tools/serve_local.py` if it isn't running) — it sends "
        "Cache-Control: no-cache on /lib/* so your edits load fresh."
    )
    # PreToolUse: warn without blocking. systemMessage shows the user; the
    # additionalContext nudges the model. We do NOT set permissionDecision, so
    # the tool call proceeds.
    out = {
        "systemMessage": msg,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": msg,
        },
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — never wedge a tool call on a guard bug
        sys.exit(0)
