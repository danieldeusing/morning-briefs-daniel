#!/usr/bin/env bash
# PostToolUse hook: rebuild the dashboard manifest after a daily newsletter file
# is written/edited, debounced so a 4-file (de/en/pt/es) brief regen triggers ONE
# rebuild instead of four.
#
# Wired from .claude/settings.json on Write|Edit. Reads the hook JSON payload on
# stdin, checks whether the touched path is a daily brief file
# (public/<category>/<lang>/YYYY-MM-DD.html), and if so schedules a coalesced
# rebuild of public/index.html via tools/build_manifest.py.
#
# Debounce strategy (last-writer-wins): each matching edit stamps a token file
# with a fresh nanosecond token and spawns a detached waiter. The waiter sleeps
# DEBOUNCE_SECONDS, then rebuilds only if its token is still the latest stamp —
# so a burst of edits collapses to a single rebuild fired by the last one.
#
# The hook always exits 0 immediately and never blocks the edit. build errors are
# appended to the log file (surfaced by the manifest-verify path / next run), not
# raised into the editing turn.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILDER="$REPO_ROOT/tools/build_manifest.py"
STATE_DIR="${TMPDIR:-/tmp}/mb-manifest-autobuild"
STAMP="$STATE_DIR/stamp"
LOG="$STATE_DIR/last-run.log"
DEBOUNCE_SECONDS="${MB_MANIFEST_DEBOUNCE:-3}"

# Path of the file the tool just wrote. Prefer jq; fall back to a tolerant grep so
# the hook still works on a machine without jq installed.
read_file_path() {
  local payload="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null
  else
    printf '%s' "$payload" \
      | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' \
      | head -1 \
      | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/'
  fi
}

payload="$(cat)"
file_path="$(read_file_path "$payload" || true)"

# Only react to daily brief files: public/<category>/<lang>/YYYY-MM-DD.html
# (lang is one of de|en|pt|es). Anything else — lib, docs, index.html itself,
# the manifest — is a no-op so we never loop on our own rebuild.
if ! printf '%s' "$file_path" | grep -qE '/public/[^/]+/(de|en|pt|es)/[0-9]{4}-[0-9]{2}-[0-9]{2}\.html$'; then
  exit 0
fi

mkdir -p "$STATE_DIR"
# Fresh coalescing token. The most recent edit in a burst wins.
token="$(date +%s%N)"
printf '%s' "$token" > "$STAMP"

# Detached waiter — survives this hook process returning. nohup + & + disown so
# the editing turn isn't held open waiting for the debounce window.
(
  sleep "$DEBOUNCE_SECONDS"
  # Rebuild only if no newer edit superseded us during the sleep.
  if [ -f "$STAMP" ] && [ "$(cat "$STAMP" 2>/dev/null)" = "$token" ]; then
    if ! python3 "$BUILDER" >"$LOG" 2>&1; then
      {
        echo "[manifest-autobuild] FAILED at $(date -u +%FT%TZ) — rebuild exited non-zero."
        echo "Run \`python3 tools/build_manifest.py\` manually to see the error."
      } >>"$LOG"
    fi
  fi
) >/dev/null 2>&1 &
disown 2>/dev/null || true

exit 0
