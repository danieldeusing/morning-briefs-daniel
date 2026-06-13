---
name: fx-snapshot
description: >
  The economy brief's daily FX ritual as one call — fetch dated EUR/BRL +
  USD/BRL + DXY (each with its real source URL and sample date), then run the
  EUR/BRL cross-check that the economy brief opens with every day: published
  EUR/BRL vs USD/BRL × EUR/USD, flagging a divergence over ~0.5 %. Wraps the
  fetch-with-fallback engine, so each value survives a 403 by stepping down its
  source ladder and NOTHING is ever fabricated — a leg whose ladder fails comes
  back ok=false so you source it by hand instead of guessing. Use this at the
  START of the economy routine, the moment you need today's FX anchors, or
  whenever you're about to write the EUR/BRL / USD/BRL / DXY figures or the
  cross-check line. Reach for it instead of hand-fetching three rates and doing
  the cross-multiply in your head — the tautology trap (deriving EUR/USD from
  the same two legs you're checking) makes a hand cross-check silently
  meaningless, and this avoids it by sourcing EUR/USD independently. Triggers:
  "fx snapshot", "today's EUR/BRL and the cross-check", "get the FX anchors for
  the economy brief", "is the ECB fix consistent with the spot cross", "DXY +
  EUR/BRL + USD/BRL for today", "run the FX ritual". Economy-specific — for any
  other single sourced number use fetch-with-fallback directly.
---

# fx-snapshot

## Why this exists

Every economy brief opens with the same three numbers and the same sanity check:

- **EUR/BRL** — the rate that prices Daniel's euro invoices in reais (ECB daily fix).
- **USD/BRL** — the dollar spot, the other leg of the cross.
- **DXY** — the dollar index, the early-warning gauge that moves *before* the real.

…and then the **cross-check**: a published EUR/BRL should be ≈ USD/BRL × EUR/USD.
When the published fix and the cross-implied value diverge by more than ~0.5 %,
that's worth a line in the brief. The 20.05 brief did exactly this — cross 5.808
vs ECB-fix 5.8347, **0.46 %**, under the line and explained by the ECB fix
sampling ~14:15 CET while the real kept moving intraday. A divergence *over* the
line usually means the two legs were sampled hours apart, or one source is stale.

Doing this by hand has two traps this skill removes:
1. **Fabrication under failure.** When a fetch 403s or a page turns into a JS
   shell, the tempting shortcut is to reuse yesterday's number. The economy
   brief-gate **blocks** an undated or fabricated FX series, and rightly so.
2. **The tautology trap.** If you compute the cross-check's EUR/USD by dividing
   the *same* EUR/BRL and USD/BRL you're checking, the implied cross is
   algebraically identical to the published rate — the check always "passes" and
   tells you nothing. The cross-check only means something when **EUR/USD comes
   from an independent source**.

This skill fetches all the legs over resilient ladders (so a failed source steps
down, and every value keeps its URL + sample date), sources EUR/USD
independently, and computes the divergence honestly.

## Run it

`scripts/fx_snapshot.py` wraps `fetch-with-fallback`'s engine. With no arguments
it uses the engine and the `sources/economy-fx.json` ladder config that ship with
that skill:

```bash
python3 .claude/skills/fx-snapshot/scripts/fx_snapshot.py
```

It prints a JSON snapshot:

```json
{
  "ok": true,
  "metrics": {
    "eurbrl": { "ok": true, "value": "5.8347", "source_url": "https://…ecb…",
                "date": "2026-05-20", "date_inferred": false, ... },
    "usdbrl": { "ok": true, "value": "5.0299", "source_url": "https://…", ... },
    "dxy":    { "ok": true, "value": "99.08",  "source_url": "https://…", ... },
    "eurusd": { "ok": true, "value": "1.16",   "source_url": "https://…", ... }
  },
  "crosscheck": {
    "computable": true,
    "published_eurbrl": 5.8347,
    "implied_eurbrl": 5.8348,
    "eurusd_used": 1.16,
    "eurusd_derived": false,        // false = independently sourced (trustworthy)
    "divergence_pct": 0.002,
    "threshold_pct": 0.5,
    "flag": false,
    "note": "Divergence 0.002% within 0.5% — consistent."
  }
}
```

Exit **0** if all three core metrics (eurbrl, usdbrl, dxy) resolved; **3** if any
core leg failed its whole ladder.

## Read the result honestly

- **`metrics.<m>.value` + `.source_url`** — the number and its citation link.
  Put both in the brief (the fx-cards and the TL;DR chip).
- **`.date` / `.date_inferred`** — the sample date. `date_inferred: true` means
  the engine could *not* pull a date from the source and filled in today's as a
  placeholder. Never present an inferred date as if the source stated it — that's
  what the gate blocks. Find a dated source or label the timing honestly.
- **`crosscheck.eurusd_derived`** — `false` means EUR/USD was fetched
  independently (the cross-check is meaningful). `true` means no `eurusd` ladder
  was configured so EUR/USD was derived from the two BRL legs — the check then
  only confirms internal arithmetic, not cross-source agreement. Prefer a config
  with an `eurusd` ladder (the shipped one has it).
- **`crosscheck.flag`** — `true` → write the divergence into the brief with the
  reason (sampling-time gap, or re-source the spot leg). `false` → the anchors
  are consistent; no caveat needed.
- **`metrics.<m>.ok: false`** — that leg's whole ladder failed; the `attempts`
  list says why each rung failed. **Do not fabricate it.** Source it by hand, or
  omit it with an honest "as of [last known]" label. DXY is the leg most likely
  to fail (it has no clean key-free source) — and the cross-check does **not**
  depend on DXY, so a missing DXY never invalidates the EUR/BRL consistency check.

## The source ladders

Live in `sources/economy-fx.json` (the fetch-with-fallback config). Metrics:
`eurbrl`, `usdbrl`, `eurusd` (key-free, ECB-backed via Frankfurter; ECB XML first
for eurbrl), and `dxy` (a TradingEconomics scrape — the page the brief already
cites). To add or reorder sources, edit that file; the rung format and the
step-down rules are documented in `fetch-with-fallback/SKILL.md`. Override the
config or engine path with `--config` / `--engine`, and the flag threshold with
`--threshold` (default 0.5).

## What this skill is NOT

It does the **economy FX trio + cross-check**, nothing else. For a single
non-FX number (a benchmark score, a gov-PDF statistic, a standing) call
`fetch-with-fallback` directly — this skill is just the economy-specific
composition of it. It is not a markets-commentary writer: it hands you trustworthy
dated numbers and a consistency verdict; the analysis is yours.
