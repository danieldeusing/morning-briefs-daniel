#!/usr/bin/env bash
# Final publish phase for the Morning Brief routine, as ONE deterministic step:
#   1. rebuild the dashboard manifest
#   2. git add + commit + push   (canonical archive on GitHub main)
#   3. deploy public/ to Cloudflare Pages  (briefs.danieldeusing.de)
#
# Why a script: the routine kept dying *between* these steps (e.g. dashboard
# rebuilt, then the run ended before it committed — generated work never
# published). Collapsing them into one call removes the agent decision-points,
# so reaching this call publishes everything. Idempotent + safe to re-run, so
# the catch-up safety net uses it to FINISH an incomplete publish without
# regenerating anything.
#
# Usage: tools/publish.sh [YYYY-MM-DD]   (defaults to today)
# Not `set -e`: a non-fatal earlier step (verify warning, push hiccup) must not
# skip the deploy — the user-facing publish is the most important step.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
DATE="${1:-$(date +%F)}"

echo "publish: [1/3] rebuilding dashboard…"
if ! python3 tools/build_manifest.py --verify; then
  echo "publish: WARN dashboard verify reported an issue — publishing anyway (a category card may render imperfectly; the brief files are unaffected)"
fi

echo "publish: [2/3] commit + push…"
git add -A
if git diff --cached --quiet; then
  echo "publish: nothing new to commit (already committed)"
else
  git commit -m "briefs $DATE"
fi
if ! git push origin main; then
  echo "publish: WARN git push failed (network/credentials) — continuing to deploy; the live site does not depend on git"
fi

echo "publish: [3/3] deploy to Cloudflare Pages…"
bash tools/deploy-cloudflare.sh
deploy_rc=$?

if [[ $deploy_rc -ne 0 ]]; then
  echo "publish: FAILED at deploy (rc=$deploy_rc) — briefs.danieldeusing.de NOT updated. Re-run 'bash tools/publish.sh $DATE' from an interactive session." >&2
  exit $deploy_rc
fi
echo "publish: done → https://briefs.danieldeusing.de (briefs $DATE)"
