---
name: recommendation-block-lint
description: >
  Lint the stocks-crypto brief's recommendation blocks to confirm each one
  carries all five mandated fields — Verdict, Why, Timeframe (tied to a dated
  event), Forecast (target range + probability + counter-scenario), and dated
  price evidence — in any of the four languages. This is Daniel's decision basis
  for real money, so a recommendation missing its timeframe, counter-scenario,
  or dated numbers is materially incomplete, not just terse. Use this AFTER you
  write or translate the stocks-crypto recommendations and BEFORE you call the
  brief done — it reads the finished HTML and tells you exactly which field is
  missing from which recommendation. Reach for it instead of re-reading six
  `callout info` blocks by eye and trying to remember the five-part contract.
  Triggers: "lint the recommendations", "check the stocks-crypto calls", "did
  every recommendation get all five fields", "recommendation-block-lint", "are
  the verdicts complete", "check the Empfehlungs-Format", "verify the
  buy/sell/hold blocks". Stocks-crypto-specific — it knows that brief's
  five-field format and its de/en/pt/es label set.
---

# recommendation-block-lint

## Why this exists

The stocks-crypto SKILL makes every recommendation a **five-part contract**
(`Empfehlungs-Format (PFLICHT)`), because the brief is Daniel's decision basis
for real investment moves. A recommendation that drops a field isn't just
terse — it's missing part of what makes it actionable:

1. **Verdict** — BUY / SELL / HOLD, carried as a `<span class="chip">`.
2. **Why** — detailed reasoning (fundamentals, catalysts, macro, ELI5 where new).
3. **Timeframe** — concrete *when*, tied to a **dated event** to wait for.
4. **Forecast** — a target range + a probability + a **counter-scenario**.
5. **Price evidence** — real, **dated** numbers (24h/7d/30d moves, levels).

Re-reading six recommendation blocks by eye, in four languages, and holding the
five-field checklist in your head is exactly the kind of mechanical check that's
easy to half-do — you notice the missing verdict but miss that the forecast has
no counter-scenario, or that the timeframe says "soon" with no dated event. This
linter does it deterministically and points at the precise gap.

It's the same spirit as the stocks-crypto **brief-gate module** (`stocks-crypto.py`),
which *blocks* only on the one liability-critical thing — a missing disclaimer.
Recommendation completeness is important but not blocking, so this is a **lint you
run and act on**, not a gate that stops the edit.

## Run it

`scripts/reco_lint.py` takes one or more brief HTML files:

```bash
# Lint all four language versions of today's brief at once:
python3 .claude/skills/recommendation-block-lint/scripts/reco_lint.py \
    public/stocks-crypto/de/2026-05-20.html \
    public/stocks-crypto/en/2026-05-20.html \
    public/stocks-crypto/pt/2026-05-20.html \
    public/stocks-crypto/es/2026-05-20.html
```

It prints a per-file report:

```
■ public/stocks-crypto/de/2026-05-20.html
  lang=de  6 recommendation(s), 1 incomplete
  ✓ Empfehlung — Öl-Exposure
  ✗ Empfehlung — Nvidia (NVDA)
      – timeframe is present but has no dated event/period (add the date or horizon to wait for)
      – forecast has no counter-scenario (add the 'else/if' case)
  …
```

Exit **0** if every recommendation in every file carries all five fields; **1**
if any field is missing — so a routine can branch on the exit code (e.g. "fix
before publishing").

## What it checks, and how it stays quiet

Each recommendation is an `<h3>…Empfehlung/Call/Recomendação/Recomendación…</h3>`
followed by a `<div class="callout info">`. The linter finds each block and
checks the five fields **by their visible label, matched per language** — it
reads the folder (`…/<lang>/…`) or `<html lang>` to pick the right label set, so
the EN/PT/ES files aren't judged against German strings.

It is deliberately tuned to favour **precision over zeal** — a lint that
cries wolf gets ignored:

- **Verdict** passes on either a `Verdict:`-style label *or* a BUY/SELL/HOLD
  chip (the brief often carries the verdict purely as a chip).
- **Timeframe** must have its label *and* a dated anchor — a date, a DD.MM, a
  period (24h/7d/Q2/H2), or a month — because "wait a while" with no date is the
  exact soft miss the format guards against.
- **Forecast** must have its label, *and* at least one price/% number, *and* a
  counter-scenario. The counter-scenario is matched broadly: the brief's house
  style is usually a **Bull/Bear/Base** tier set (each with a probability), but a
  conditional ("unless X", "ohne X weiter abwärts") or a named downside counts
  too.
- **Price evidence** checks **substance, not label**: a real price/% figure plus
  a date anchor. It does *not* nag about a missing "Beleg:"/"Preço:" label when
  the dated numbers are plainly present — a label-only complaint is noise.

This is why a complete, real brief lints clean in all four languages, while a
block that genuinely drops a field is caught with a specific, actionable message.

## What this skill is NOT

It checks **structure and completeness**, not investment correctness — it cannot
tell you whether HOLD is the *right* call, only that the call is fully stated. It
also doesn't write or fix the recommendations; it tells you which field to add,
and you write it. And it's stocks-crypto-specific: the five-field contract and
the label set are that brief's. (Note: nothing here constitutes financial advice;
the brief's own disclaimer — enforced by the brief-gate — still applies.)
