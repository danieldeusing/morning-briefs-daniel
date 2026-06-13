#!/usr/bin/env python3
"""Self-check for trizone.py. Run: python3 test_trizone.py  (exit 0 = pass).

The load-bearing property is DST correctness: the same European wall-clock time
must map to a DIFFERENT Brazil time in winter vs summer, because Brazil keeps no
DST and Europe does. A naive hardcoded-offset converter would produce the SAME
BRT both seasons — so the winter≠summer assertion below is the negative test:
it fails loudly for exactly the bug this skill exists to prevent.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trizone import convert  # noqa: E402

failures = []


def check(label, got, want):
    ok = got == want
    print(f"  [{'✓' if ok else '✗'}] {label}: {got!r}" + ("" if ok else f"  (want {want!r})"))
    if not ok:
        failures.append(label)


# 1. Winter Bundesliga kickoff: 21:00 MEZ → 17:00 BRT (4h gap, MEZ label).
w = convert("21:00", "2026-01-17", "berlin", None)
check("winter football_string", w["football_string"], "21:00 MEZ / 17:00 BRT")

# 2. Summer kickoff, SAME wall-clock: 21:00 MESZ → 16:00 BRT (5h gap, MESZ label).
s = convert("21:00", "2026-06-17", "berlin", None)
check("summer football_string", s["football_string"], "21:00 MESZ / 16:00 BRT")

# 3. THE NEGATIVE TEST — winter and summer BRT must differ. If they were equal,
#    the converter is using a fixed offset and would mislabel half the season.
brt_w, brt_s = w["brt"]["time"], s["brt"]["time"]
neg_ok = brt_w != brt_s
print(f"  [{'✓' if neg_ok else '✗'}] DST flips BRT (winter {brt_w} != summer {brt_s})")
if not neg_ok:
    failures.append("dst-flip")

# 4. Europe label tracks the season, not a constant.
check("winter EU label", w["europe"]["label"], "MEZ")
check("summer EU label", s["europe"]["label"], "MESZ")

# 5. Motorsport three-zone for a non-European venue (Canada GP, Montreal EDT).
m = convert("14:00", "2026-06-14", "et", "et")
check("motorsport_string (Montreal)", m["motorsport_string"], "14:00 EDT / 15:00 BRT / 20:00 CEST")

if failures:
    print(f"\nFAIL: {len(failures)} check(s) failed: {', '.join(failures)}")
    sys.exit(1)
print("\nOK: all trizone checks pass (DST correctness verified).")
