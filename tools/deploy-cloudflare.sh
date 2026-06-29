#!/usr/bin/env bash
# Deploy the Morning Brief static site (public/) to Cloudflare Pages.
#
# Project: "briefs" (production branch "prod") → https://briefs.danieldeusing.de
# Auth:    Cloudflare API token + Account ID, read from 1Password via the
#          workspace service-account token (never hard-coded, never committed).
#
# Used by the consolidated morning-brief routine as its final publish step, and
# runnable by hand: tools/deploy-cloudflare.sh
#
# Exit codes: 0 = deployed, non-zero = failed (the routine surfaces the failure).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_ENV="${MB_WORKSPACE_ENV:-$REPO_ROOT/../../.env}"
PROJECT_NAME="briefs"
PROD_BRANCH="prod"

cd "$REPO_ROOT"

if [[ ! -d public ]]; then
  echo "deploy-cloudflare: public/ not found in $REPO_ROOT" >&2
  exit 1
fi

if [[ ! -f "$WORKSPACE_ENV" ]]; then
  echo "deploy-cloudflare: workspace .env not found at $WORKSPACE_ENV" >&2
  exit 1
fi

# Cloudflare Pages-Edit token + Account ID.
# PRIMARY: read straight from the workspace .env (op-free). This is what makes
# UNATTENDED deploys reliable — `op` (1Password CLI) intermittently HANGS in
# headless/cron runs (its desktop-daemon auth path blocks), and being a Go binary
# it ignores SIGALRM so it can't be timed out cleanly. Reading the cached creds
# from .env skips op entirely. Re-cache them with:
#   op item get 'cloudflare - daniedeusing - api token' --vault danieldeusing-agents \
#     --fields password --reveal   (and --fields 'Account ID')  >> ../../.env  as
#   CLOUDFLARE_API_TOKEN=… / CLOUDFLARE_ACCOUNT_ID=…
# FALLBACK: if they're not in .env, fetch from 1Password via op, guarded by a
# kill -9 watchdog (SIGKILL is the only signal op can't ignore; op writes the
# value out fast and only hangs on exit, so the kill lands after it's captured).
CLOUDFLARE_API_TOKEN="$(grep -E '^CLOUDFLARE_API_TOKEN=' "$WORKSPACE_ENV" | cut -d= -f2-)"
CLOUDFLARE_ACCOUNT_ID="$(grep -E '^CLOUDFLARE_ACCOUNT_ID=' "$WORKSPACE_ENV" | cut -d= -f2-)"

if [[ -z "$CLOUDFLARE_API_TOKEN" || -z "$CLOUDFLARE_ACCOUNT_ID" ]]; then
  echo "deploy-cloudflare: Cloudflare creds not in .env — falling back to 1Password (op)…" >&2
  OP_SERVICE_ACCOUNT_TOKEN="$(grep '^OP_SERVICE_TOKEN=' "$WORKSPACE_ENV" | cut -d= -f2-)"
  export OP_SERVICE_ACCOUNT_TOKEN
  if [[ -z "$OP_SERVICE_ACCOUNT_TOKEN" ]]; then
    echo "deploy-cloudflare: OP_SERVICE_TOKEN also missing from $WORKSPACE_ENV" >&2
    exit 1
  fi
  op_field() {
    local out; out="$(mktemp)"
    op item get 'cloudflare - daniedeusing - api token' \
      --vault danieldeusing-agents --fields "$1" --reveal >"$out" 2>/dev/null &
    local op_pid=$!
    ( command sleep 25; kill -9 "$op_pid" 2>/dev/null ) &
    local watchdog_pid=$!
    local rc=0
    wait "$op_pid" 2>/dev/null || rc=$?
    kill "$watchdog_pid" 2>/dev/null; wait "$watchdog_pid" 2>/dev/null || true
    cat "$out"; rm -f "$out"
    return "$rc"
  }
  if [[ -z "$CLOUDFLARE_API_TOKEN"  ]]; then CLOUDFLARE_API_TOKEN="$(op_field password)" || true; fi
  if [[ -z "$CLOUDFLARE_ACCOUNT_ID" ]]; then CLOUDFLARE_ACCOUNT_ID="$(op_field 'Account ID')" || true; fi
fi

export CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID
if [[ -z "$CLOUDFLARE_API_TOKEN" || -z "$CLOUDFLARE_ACCOUNT_ID" ]]; then
  echo "deploy-cloudflare: could not obtain Cloudflare token/account (.env or 1Password)" >&2
  exit 1
fi

echo "deploy-cloudflare: deploying public/ → Pages project '$PROJECT_NAME' (branch $PROD_BRANCH)…"
npx --yes wrangler@4 pages deploy public \
  --project-name "$PROJECT_NAME" \
  --branch "$PROD_BRANCH" \
  --commit-dirty=true

echo "deploy-cloudflare: done → https://briefs.danieldeusing.de"
