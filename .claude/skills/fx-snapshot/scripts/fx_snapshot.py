#!/usr/bin/env python3
"""fx-snapshot — the economy brief's daily FX ritual as one call.

Every economy brief opens with the same three numbers and the same sanity check:
  • EUR/BRL  — the figure that prices Daniel's euro invoices in reais (ECB daily fix)
  • USD/BRL  — the dollar spot, the other side of the cross
  • DXY      — the dollar index, the early-warning gauge that moves *before* the real

…and then a CROSS-CHECK: EUR/BRL should ≈ USD/BRL × EUR/USD. If the published
EUR/BRL and the cross-implied EUR/BRL diverge by more than ~0.5 %, that's worth a
flag in the brief (the 20.05 brief did exactly this: cross 5.808 vs ECB-fix
5.8347, 0.46 % — under the line, and explained by the ECB fix sampling ~14:15 CET
while the real moved intraday after). A divergence over the line usually means
the two legs were sampled at very different times, or one source is stale.

This wraps `fetch-with-fallback`'s engine: it runs the engine once per metric
(so each value keeps its real source URL + sample date and survives a 403 by
stepping down its ladder), then layers the cross-check on top. It never invents a
number — a metric whose whole ladder failed comes back ok=false, and the
cross-check is simply skipped if a leg is missing.

The EUR/USD leg: if the config has a `eurusd` ladder it's fetched; otherwise it's
derived from the EUR/BRL and USD/BRL we already have (eurusd = eurbrl / usdbrl),
which is enough to sanity-check internal consistency. The cross is computed as
usdbrl × eurusd.

CLI:
    fx_snapshot.py [--config <fx-config.json>] [--engine <fetch_engine.py>] \
                   [--threshold 0.5]
Defaults point at the fetch-with-fallback engine and sources/economy-fx.json.
Prints a JSON snapshot. Exit 0 if all three core metrics resolved, 3 if any
core metric (eurbrl/usdbrl/dxy) failed its whole ladder — so the routine knows
to source that leg by hand rather than ship a hole.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS_DIR = HERE.parent.parent          # .claude/skills/fx-snapshot/scripts → .claude/skills
DEFAULT_ENGINE = SKILLS_DIR / "fetch-with-fallback" / "scripts" / "fetch_engine.py"
DEFAULT_CONFIG = SKILLS_DIR / "fetch-with-fallback" / "sources" / "economy-fx.json"

CORE_METRICS = ("eurbrl", "usdbrl", "dxy")


def run_engine(engine: Path, config: Path, key: str) -> dict:
    """Invoke fetch_engine.py for one metric; return its result dict. A non-zero
    exit (all rungs failed) still yields a parseable {ok:false,...} on stdout."""
    try:
        proc = subprocess.run(
            [sys.executable, str(engine), str(config), "--key", key],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "value": None, "error": f"engine call failed: {e}"}
    out = (proc.stdout or "").strip()
    if not out:
        return {"ok": False, "value": None,
                "error": f"engine produced no output (stderr: {proc.stderr.strip()[:200]})"}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "value": None,
                "error": f"engine output not JSON: {out[:200]}"}


def _to_float(result: dict):
    """Pull a float out of an engine result, tolerant of '5,8347' (comma
    decimal) and stray thousands separators. Returns None if not numeric."""
    if not result.get("ok"):
        return None
    raw = str(result.get("value", "")).strip()
    # Normalise: if both separators present, assume '.'=thousands, ','=decimal
    # (European); else a lone ',' is the decimal point.
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def build_snapshot(engine: Path, config: Path, threshold_pct: float) -> dict:
    # Load config so we know which optional metrics (eurusd) are available.
    try:
        cfg = json.loads(config.read_text(encoding="utf-8"))
        cfg_keys = set(cfg) if isinstance(cfg, dict) else set()
    except (OSError, json.JSONDecodeError):
        cfg_keys = set()

    metrics: dict[str, dict] = {}
    for key in CORE_METRICS:
        if key in cfg_keys:
            metrics[key] = run_engine(engine, config, key)
        else:
            metrics[key] = {"ok": False, "value": None,
                            "error": f"no '{key}' ladder in {config.name} — "
                                     "add one (see fetch-with-fallback README)."}

    # EUR/USD: prefer a real ladder; else derive from the two BRL legs.
    eurusd_result = None
    if "eurusd" in cfg_keys:
        eurusd_result = run_engine(engine, config, "eurusd")
        metrics["eurusd"] = eurusd_result

    eurbrl = _to_float(metrics["eurbrl"])
    usdbrl = _to_float(metrics["usdbrl"])
    eurusd = _to_float(eurusd_result) if eurusd_result else None
    eurusd_derived = False
    if eurusd is None and eurbrl is not None and usdbrl not in (None, 0):
        eurusd = eurbrl / usdbrl
        eurusd_derived = True

    # Cross-check: published EUR/BRL vs cross-implied (usdbrl × eurusd).
    crosscheck = {"computable": False}
    if eurbrl is not None and usdbrl is not None and eurusd is not None:
        implied = usdbrl * eurusd
        divergence_pct = abs(implied - eurbrl) / eurbrl * 100 if eurbrl else None
        crosscheck = {
            "computable": True,
            "published_eurbrl": round(eurbrl, 4),
            "implied_eurbrl": round(implied, 4),
            "eurusd_used": round(eurusd, 4),
            "eurusd_derived": eurusd_derived,
            "divergence_pct": round(divergence_pct, 3) if divergence_pct is not None else None,
            "threshold_pct": threshold_pct,
            "flag": bool(divergence_pct is not None and divergence_pct > threshold_pct),
        }
        if crosscheck["flag"]:
            crosscheck["note"] = (
                f"Divergence {crosscheck['divergence_pct']}% exceeds "
                f"{threshold_pct}% — legs likely sampled at different times, or a "
                "source is stale. Explain it in the brief or re-source the spot leg."
            )
        else:
            crosscheck["note"] = (
                f"Divergence {crosscheck['divergence_pct']}% within "
                f"{threshold_pct}% — consistent."
            )
    else:
        missing = [k for k, v in (("eurbrl", eurbrl), ("usdbrl", usdbrl),
                                  ("eurusd", eurusd)) if v is None]
        crosscheck["note"] = (f"Cross-check skipped — missing {', '.join(missing)}. "
                              "Do not fabricate the missing leg.")

    all_core_ok = all(metrics[k].get("ok") for k in CORE_METRICS)
    return {
        "ok": all_core_ok,
        "metrics": metrics,
        "crosscheck": crosscheck,
        "config": str(config),
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="fx_snapshot.py",
        description="Fetch dated EUR/BRL + USD/BRL + DXY and run the EUR/BRL "
                    "cross-check, wrapping the fetch-with-fallback engine.")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG),
                    help="FX source config (metric → ladder). "
                         f"Default: {DEFAULT_CONFIG}")
    ap.add_argument("--engine", default=str(DEFAULT_ENGINE),
                    help=f"fetch_engine.py path. Default: {DEFAULT_ENGINE}")
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="cross-check divergence flag threshold in %% (default 0.5)")
    args = ap.parse_args(argv)

    engine = Path(args.engine)
    config = Path(args.config)
    if not engine.exists():
        print(json.dumps({"ok": False, "error": f"engine not found: {engine}"}))
        return 2
    if not config.exists():
        print(json.dumps({"ok": False, "error": f"config not found: {config}"}))
        return 2

    snap = build_snapshot(engine, config, args.threshold)
    print(json.dumps(snap, ensure_ascii=False, indent=2))
    return 0 if snap["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
