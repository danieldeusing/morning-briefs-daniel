---
name: conjugation-verify
description: >
  Drive the learn-language verb-conjugation self-check: for each verb the brief
  teaches, emit the canonical conjugator URL to open (verbformen.de for DE,
  conjugacao.com.br for PT, Reverso/RAE for ES), the exact paradigm cells to verify
  (persons × tenses, with NO vós / NO vosotros), and the KNOWN irregularity traps
  that lemma trips — then validate the forms you pulled against those trap rules.
  It does NOT scrape (conjugators are JS-heavy and rot); it tells you what to fetch
  and catches the specific high-value mistakes by spelling rule. Run it at the START
  of building the day's conjugation tables, the moment you have the verb list, and
  again with --validate once you've filled the forms. Reach for it instead of doing
  ten-plus per-verb conjugator lookups by hand and eyeballing whether the o→ue
  diphthong, the c→qu preterite, or the sein-auxiliary is right. Triggers: "verify
  the conjugations", "conjugation self-check", "which conjugator for this verb",
  "check the verb tables", "did I get the stem change right", "conjugation-verify",
  "is aufwachen sein or haben". learn-language-specific (DE/PT/ES verbs).
---

# conjugation-verify

## Why this exists

The learn-language brief teaches ≥10 verbs/day, each with a full DE/PT/ES
conjugation table. The routine's "Konjugator-Modell" step mandates verifying every
verb against an authoritative conjugator rather than writing forms from memory —
because a wrong stem vowel (`*consolo` for `consuelo`), a missed orthographic shift
(`*buscei` for `busquei`), or the wrong perfect auxiliary (`*ich habe aufgewacht`)
ships silently into a *teaching* newsletter and quietly teaches the reader the wrong
thing. Doing that check by hand across ten-plus verbs in three languages is slow,
easy to skip under time pressure, and easy to eyeball-miss the exact cells that
matter.

This skill does the durable half of that check. It is deliberately **not an
auto-scraper** — conjugator sites are JS-heavy, differ from each other, and a parser
keyed to their markup would rot the first time one redesigns. Instead it pins down
the two parts that *are* stable: **where to look** (the canonical URL + the precise
cells) and **what's easy to get wrong** (a curated table of the recurring
irregularity traps, each checkable by spelling). You fetch the one URL it gives you
and fill the table from verified data; it flags the traps so you don't miss them,
then re-checks your filled forms.

## Two modes

### PLAN (default) — what to fetch, and the traps to watch

```bash
cd /Users/daniel/Work/danieldeusing/morning-briefs/daniel
python3 .claude/skills/conjugation-verify/scripts/conjugation_verify.py \
  --verbs "consolar:es,trocar:pt,aufwachen:de" --pretty
```

Per verb you get the conjugator `name` + `url` (reflexives resolve to the bare
infinitive — `vestirse` → `…-vestir…`), the `verify_cells` string (the persons ×
tenses your table uses, with the **NO vós** / **NO vosotros** reminder baked in),
and a `traps` list — e.g. for `consolar:es`:

> **stem-change o→ue (stressed)** — yo/tú/él/ellos present diphthongize (consuelo);
> but nosotros keeps the bare stem (consolamos). Subjunctive follows (consuele).

Open each `url`, read the cells, fill your table. An unknown verb still gets the URL
+ cells (just no trap flags) — always useful.

### VALIDATE (`--validate`) — check the forms you pulled

After filling the forms, hand them back as JSON and let the rules re-check them:

```bash
python3 .claude/skills/conjugation-verify/scripts/conjugation_verify.py \
  --verbs "consolar:es,aufwachen:de" \
  --validate --forms /tmp/pulled-forms.json --pretty
```

`--forms` is a list of `{"lemma","lang","forms": {…}}`. The `forms` keys the
validators look at (supply what's relevant; unsupplied = unchecked, not a failure):

| key           | meaning                                  |
|---------------|------------------------------------------|
| `1sg_pres`    | 1st-person-singular present (yo/eu/ich)  |
| `1pl_pres`    | 1st-person-plural present (nosotros/nós/wir) |
| `1sg_pret`    | 1sg preterite (busqué / busquei)         |
| `3sg_pret`    | 3sg preterite (vistió)                   |
| `perfect_aux` | DE Perfekt auxiliary (sein / haben)      |

It flags only the curated traps — a `1sg_pres` that doesn't diphthongize on an
o→ue verb, a `-car` preterite not spelled `-qué`/`-quei`, a movement verb whose
`perfect_aux` is `haben`, etc. Exit **1** if any rule is violated, **0** if clean.

### Exit codes

- **0** — PLAN emitted, or VALIDATE found no rule violations.
- **1** — VALIDATE found ≥1 form that violates a known trap rule (read `issues`).
- **2** — bad usage: no verbs, unparseable `--verbs`/`--json`/`--forms`, unknown lang.

## What it knows (the trap table)

Curated, not exhaustive — the recurring gotchas this brief teaches:

- **ES** — stem-changers o→ue (`consolar`, `dormir`, …) and e→ie (`despertar`, …)
  that diphthongize under stress but keep the **bare stem in nosotros**; e→i
  (`vestir`, `pedir`); orthographic c→qu (`-car`), g→gu (`-gar`), g→j (`-ger/-gir`,
  e.g. `recojo`). Plus the `recoger ≠ buscar` false-friend note.
- **PT** — orthographic c→qu (`-car`: `busquei`, `troquei`), g→gu (`-gar`:
  `briguei`); stem-vowel raise (`vestir`→`visto`, `dormir`→`durmo`).
- **DE** — Perfekt-with-`sein` movement/change-of-state verbs (`aufwachen` → `ich
  bin aufgewacht`); strong/ablaut verbs (`streiten`→`stritt`→`gestritten`).

Unknown verbs pass through with URL + cells and no trap flags; the validator only
asserts what it knows, so it never blocks a correct-but-unmodeled verb.

## Verifying it (fixtures)

```bash
cd /Users/daniel/Work/danieldeusing/morning-briefs/daniel
SK=.claude/skills/conjugation-verify

# PLAN across every trap type
python3 "$SK/scripts/conjugation_verify.py" \
  --verbs "consolar:es,despertarse:es,vestirse:es,recoger:es,trocar:pt,brigar:pt,aufwachen:de,streiten:de" --pretty

# VALIDATE a fixture with two planted errors → exit 1, flags consolar + aufwachen
python3 "$SK/scripts/conjugation_verify.py" \
  --verbs "consolar:es,despertarse:es,trocar:pt,brigar:pt,recoger:es,aufwachen:de" \
  --validate --forms "$SK/fixtures/forms-with-errors.json" --pretty ; echo "exit $?"

# VALIDATE the all-correct fixture → exit 0, no issues
python3 "$SK/scripts/conjugation_verify.py" \
  --verbs "consolar:es,despertarse:es,trocar:pt,aufwachen:de" \
  --validate --forms "$SK/fixtures/forms-correct.json" ; echo "exit $?"
```

`fixtures/forms-with-errors.json` plants `consolar` 1sg-present `consolo` (missing
o→ue) and `aufwachen` `perfect_aux: haben` (should be sein); the validator flags
exactly those two and passes the correct forms. `fixtures/forms-correct.json` is the
same set fixed, and validates clean.

## How the learn-language routine uses this

In the "Konjugator-Modell" step: collect the day's verb list, run PLAN, open each
returned `url` and fill the DE/PT/ES tables from the verified cells (heeding the
trap notes and the NO-vós / NO-vosotros reminder). Before saving, run `--validate`
with the forms you pulled as a last guard against a planted-back typo. Pairs with the
learn-language brief-gate: PLAN sources the forms, VALIDATE asserts the ones most
likely to be wrong.
