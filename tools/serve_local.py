#!/usr/bin/env python3
"""Local no-cache static server for verifying brief/lib changes — :8090.

Replaces the old `news-static` Docker container (the site now lives on Cloudflare
Pages, so there is no persistent local server). Start this on demand when you need
to verify a change in a real browser (the `responsive-spacing-check` and
`lib-component-scaffold` skills, the print/Drucken flow, etc.):

    python3 tools/serve_local.py            # serves public/ on http://localhost:8090/
    python3 tools/serve_local.py --port 9000

Why :8090 and why no-cache: lib edits (`public/lib/styles.css|newsletter.js`) are
shared by every brief. A plain static server with no cache headers lets the
browser reuse a STALE lib, so a lib change verifies green/red against the OLD
file. This server sends `Cache-Control: no-cache` on `/lib/*` so the browser
revalidates and your edit always loads fresh — the same contract the retired
Caddy edge provided. The `stale_lib_port_guard` hook still nudges you to verify
on :8090 rather than the preview default (:8765, which caches).

Stdlib only. Ctrl-C to stop.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = REPO_ROOT / "public"


class NoCacheLibHandler(SimpleHTTPRequestHandler):
    """Serve public/ but force revalidation of the shared lib so edits load fresh."""

    def end_headers(self) -> None:
        # Shared lib (CSS/JS/fonts) must never be served stale during verification.
        if self.path.startswith("/lib/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:  # quieter console
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Local no-cache server for public/.")
    parser.add_argument("--port", type=int, default=8090, help="port (default 8090)")
    args = parser.parse_args()

    if not PUBLIC_DIR.is_dir():
        print(f"serve_local: public/ not found at {PUBLIC_DIR}")
        return 1

    handler = partial(NoCacheLibHandler, directory=str(PUBLIC_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"serve_local: http://localhost:{args.port}/  (public/ with no-cache on /lib/*) — Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nserve_local: stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
