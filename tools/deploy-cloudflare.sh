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

# 1Password service-account token (workspace .env) drives the op CLI.
if [[ ! -f "$WORKSPACE_ENV" ]]; then
  echo "deploy-cloudflare: workspace .env not found at $WORKSPACE_ENV" >&2
  exit 1
fi
OP_SERVICE_ACCOUNT_TOKEN="$(grep '^OP_SERVICE_TOKEN=' "$WORKSPACE_ENV" | cut -d= -f2-)"
export OP_SERVICE_ACCOUNT_TOKEN
if [[ -z "$OP_SERVICE_ACCOUNT_TOKEN" ]]; then
  echo "deploy-cloudflare: OP_SERVICE_TOKEN missing from $WORKSPACE_ENV" >&2
  exit 1
fi

# Cloudflare Pages-Edit token + Account ID from the danieldeusing-agents vault.
# Wrap `op` in a hard 60s timeout: it intermittently HANGS in headless/cron runs,
# which used to silently stall the entire deploy (git push had already succeeded,
# so the failure went unnoticed and the live site went stale). macOS has no
# timeout(1), so use perl's alarm — the timer survives exec and SIGALRM kills op
# on expiry. A hang now fails fast (empty output) → the guard below exits 1.
op_field() {
  perl -e 'alarm shift @ARGV; exec @ARGV' 60 \
    op item get 'cloudflare - daniedeusing - api token' \
    --vault danieldeusing-agents --fields "$1" --reveal 2>/dev/null
}
CLOUDFLARE_API_TOKEN="$(op_field password)" || true
CLOUDFLARE_ACCOUNT_ID="$(op_field 'Account ID')" || true
export CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID
if [[ -z "$CLOUDFLARE_API_TOKEN" || -z "$CLOUDFLARE_ACCOUNT_ID" ]]; then
  echo "deploy-cloudflare: could not read Cloudflare token/account from 1Password (op timed out or failed)" >&2
  exit 1
fi

echo "deploy-cloudflare: deploying public/ → Pages project '$PROJECT_NAME' (branch $PROD_BRANCH)…"
npx --yes wrangler@4 pages deploy public \
  --project-name "$PROJECT_NAME" \
  --branch "$PROD_BRANCH" \
  --commit-dirty=true

echo "deploy-cloudflare: done → https://briefs.danieldeusing.de"
