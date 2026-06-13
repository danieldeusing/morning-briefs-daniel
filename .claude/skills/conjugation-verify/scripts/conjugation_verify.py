#!/usr/bin/env python3
"""Plan and check the learn-language verb-conjugation self-check.

The learn-language brief teaches ≥10 verbs/day, each with a full conjugation table
in DE/PT/ES. Those forms must be *verified against an authoritative conjugator*, not
written from memory — a wrong stem vowel or a missed orthographic shift ships
silently into a teaching newsletter and quietly teaches the reader the wrong form.
The routine's "Konjugator-Modell" step already mandates a per-verb live check
against conjugacao.com.br (PT) / reverso/RAE (ES) / verbformen.de (DE); doing that
by hand for ten-plus verbs across three languages is slow, easy to skip under time
pressure, and easy to eyeball-miss the exact traps that matter.

This skill does the durable, low-rot half of that check. It is NOT an auto-scraper —
conjugators are JS-heavy and differ per site, and a brittle parser would rot. Instead
it:

  1. PLAN (default): for each (lemma, lang) emits the canonical conjugator URL to
     open, the exact paradigm cells to verify (the persons × tenses the brief's
     table uses), and — crucially — any KNOWN IRREGULARITY TRAPS that lemma trips,
     pulled from a built-in rule table. The agent then fetches that one URL and fills
     the table from verified data, with the traps called out so they're not missed.

  2. VALIDATE (--validate): given the forms the agent pulled (a small JSON), checks
     them against the trap rules and flags any that look wrong (e.g. a Spanish
     o→ue stem-changer whose "yo" form has no diphthong, a PT -car verb whose
     1sg-preterite isn't spelled -quei). It does not invent forms — it only catches
     the specific, high-value mistakes the routine has hit before.

The trap table is deliberately small and curated: the recurring gotchas this brief
teaches, each with a citation to the rule, not an exhaustive grammar. Unknown verbs
simply get the URL + cell checklist with no trap flags (still useful), and the
validator passes them through (it only asserts what it knows).

Inputs:
  --verbs "lemma:lang,lemma:lang,…"   e.g. "consolar:es,trocar:pt,aufwachen:de"
                                       lang ∈ de | pt | es
  --json PATH                          alternatively, a JSON list of {"lemma","lang"}
  (PLAN reads the verb list; VALIDATE additionally reads --forms)

  --validate                           switch to check mode
  --forms PATH                         JSON of agent-pulled forms to validate, shape:
        [{"lemma","lang","forms": {"1sg_pres": "...", "1sg_pret": "...", ...}}, …]

Output: JSON to stdout (--pretty for indented).

Exit codes:
  0  PLAN emitted, or VALIDATE found no rule violations
  1  VALIDATE found at least one form that violates a known trap rule
  2  bad usage (no verbs, unparseable --verbs/--json/--forms, unknown lang)
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

LANGS = {"de", "pt", "es"}

# Canonical conjugator per language. {lemma} is URL-substituted (lower-cased; for
# reflexives the routine passes the bare verb, e.g. "vestir" not "vestirse", since
# the conjugator pages key on the non-reflexive infinitive).
CONJUGATORS = {
    "de": {
        "name": "verbformen.de",
        "url": "https://www.verbformen.de/konjugation/{lemma}.htm",
        "cells": "Präsens, Präteritum, Perfekt (Hilfsverb!), Futur I, Konjunktiv II — "
                 "ich · du · er/sie/es · wir · ihr · sie/Sie",
    },
    "pt": {
        "name": "conjugacao.com.br",
        "url": "https://www.conjugacao.com.br/verbo-{lemma}/",
        "cells": "Presente, Pretérito perfeito, Pretérito imperfeito, Futuro do "
                 "presente, Presente do subjuntivo — eu · você · ele/ela · nós · vocês "
                 "(NO vós row)",
    },
    "es": {
        "name": "Reverso Conjugación (cross-check RAE/conjugacion.es)",
        "url": "https://conjugator.reverso.net/conjugation-spanish-verb-{lemma}.html",
        "cells": "Presente, Pretérito indefinido, Pretérito imperfecto, Futuro, "
                 "Presente de subjuntivo — yo · tú · él/ella/usted · nosotros · ustedes "
                 "(NO vosotros row)",
    },
}

# ── Irregularity trap table ──────────────────────────────────────────────────
# Each trap: a matcher (lang + lemma test) → a human note + an optional validator
# that inspects agent-supplied `forms` and returns an error string when violated.
# Kept curated: the recurring gotchas this brief teaches. `forms` keys the validators
# look at: 1sg_pres, 1sg_pret, 3sg_pret, 1pl_pres, perfect_aux (de), etc.

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def _es_o_ue_stems():
    # Spanish o→ue stem-changers seen in this brief (and common kin). The "yo"
    # present must diphthongize (consuelo, duermo), but "nosotros" must NOT (keeps
    # the bare stem: consolamos, dormimos).
    return {"consolar", "dormir", "contar", "acostar", "acostarse", "soñar", "volar"}


def _es_e_ie_stems():
    return {"despertar", "despertarse", "querer", "pensar", "empezar", "sentar",
            "sentarse", "perder"}


def _es_e_i_stems():
    return {"vestir", "vestirse", "pedir", "servir", "repetir", "medir"}


def base_lemma(lemma: str) -> str:
    """Strip a trailing reflexive -se for matching (vestirse → vestir)."""
    l = lemma.strip().lower()
    return l[:-2] if l.endswith("se") and len(l) > 3 else l


def traps_for(lemma: str, lang: str) -> list[dict]:
    """Return the list of trap dicts that apply to (lemma, lang)."""
    l = base_lemma(lemma)
    out: list[dict] = []

    if lang == "es":
        if l in _es_o_ue_stems():
            out.append({
                "trap": "stem-change o→ue (stressed)",
                "note": "yo/tú/él/ellos present diphthongize (o→ue: consuelo, duermo); "
                        "but nosotros/vosotros keep the bare stem (consolamos, dormimos). "
                        "Subjunctive follows the present (consuele).",
                "_check": ("1sg_pres", "ue", "1pl_pres", "no-ue"),
            })
        if l in _es_e_ie_stems():
            out.append({
                "trap": "stem-change e→ie (stressed)",
                "note": "yo/tú/él/ellos present diphthongize (e→ie: despierto); "
                        "nosotros keeps the bare stem (despertamos).",
                "_check": ("1sg_pres", "ie", "1pl_pres", "no-ie"),
            })
        if l in _es_e_i_stems():
            out.append({
                "trap": "stem-change e→i",
                "note": "e→i in present (yo me visto) and 3rd-person preterite "
                        "(él se vistió, ellos vistieron).",
                "_check": ("1sg_pres", "e->i-pres", None, None),
            })
        if l.endswith("car"):
            out.append({
                "trap": "orthographic c→qu before e",
                "note": "1sg preterite is -qué (busqué, not *buscé); present subjunctive "
                        "-que (busque). Sound /k/ preserved before e.",
                "_check": ("1sg_pret", "es-car-pret", None, None),
            })
        if l.endswith("gar"):
            out.append({
                "trap": "orthographic g→gu before e",
                "note": "1sg preterite -gué (llegué); subjunctive -gue (llegue).",
                "_check": ("1sg_pret", "es-gar-pret", None, None),
            })
        if l.endswith("ger") or l.endswith("gir"):
            out.append({
                "trap": "orthographic g→j before o/a",
                "note": "1sg present -jo (recojo, not *recogo); subjunctive -ja (recoja). "
                        "Note recoger ≠ buscar — 'buscar' means to search, not to fetch.",
                "_check": ("1sg_pres", "es-ger-pres", None, None),
            })

    if lang == "pt":
        if l.endswith("car"):
            out.append({
                "trap": "orthographic c→qu before e",
                "note": "1sg preterite -quei (busquei, troquei, not *buscei); present "
                        "subjunctive -que (busque). Sound /k/ preserved before e.",
                "_check": ("1sg_pret", "pt-car-pret", None, None),
            })
        if l.endswith("gar"):
            out.append({
                "trap": "orthographic g→gu before e",
                "note": "1sg preterite -guei (briguei, cheguei); subjunctive -gue (brigue).",
                "_check": ("1sg_pret", "pt-gar-pret", None, None),
            })
        if l in {"vestir", "pedir", "servir", "repetir", "dormir"}:
            out.append({
                "trap": "stem vowel raise (e→i / o→u)",
                "note": "1sg present raises (eu visto, eu durmo) and the present "
                        "subjunctive follows (que ele vista, que ele durma).",
                "_check": (None, None, None, None),
            })

    if lang == "de":
        if l in {"aufwachen", "einschlafen", "aufstehen", "wachsen", "fallen",
                 "gehen", "kommen", "laufen", "reisen", "passieren"}:
            out.append({
                "trap": "Perfekt with sein (not haben)",
                "note": "Movement / change-of-state verb → Perfekt uses sein: "
                        "'ich bin aufgewacht', not *'ich habe aufgewacht'.",
                "_check": ("perfect_aux", "de-sein", None, None),
            })
        if l in {"streiten", "schlafen", "schreiben", "bleiben", "ziehen", "gehen",
                 "trinken", "singen", "finden"}:
            out.append({
                "trap": "strong/irregular verb",
                "note": "Strong verb — vowel-change preterite/participle (streiten → "
                        "stritt → gestritten; schlafen → schlief → geschlafen). Verify the "
                        "exact ablaut, don't regularize.",
                "_check": (None, None, None, None),
            })
    return out


# ── validators ───────────────────────────────────────────────────────────────

def _violation(kind: str, lemma: str, forms: dict) -> str | None:
    """Return an error string if `forms` violates the trap `kind`, else None.
    Only asserts what's safely checkable from spelling; silent (None) when the
    needed form isn't supplied — absence isn't a violation, it's just unchecked."""
    g = lambda k: (forms.get(k) or "").strip().lower()

    if kind == "ue":  # 1sg present must contain 'ue'
        v = g("1sg_pres")
        if v and "ue" not in v:
            return f"{lemma}: 1sg present '{v}' should diphthongize o→ue (e.g. consuelo/duermo)"
    elif kind == "no-ue":  # 1pl present must NOT diphthongize
        v = g("1pl_pres")
        if v and "ue" in v:
            return f"{lemma}: 1pl present '{v}' should keep the bare stem (no ue: consolamos/dormimos)"
    elif kind == "ie":
        v = g("1sg_pres")
        if v and "ie" not in v:
            return f"{lemma}: 1sg present '{v}' should diphthongize e→ie (e.g. despierto)"
    elif kind == "no-ie":
        v = g("1pl_pres")
        if v and "ie" in v:
            return f"{lemma}: 1pl present '{v}' should keep the bare stem (no ie: despertamos)"
    elif kind == "e->i-pres":
        # crude: the present should show 'i' where the infinitive had stressed 'e'
        v = g("1sg_pres")
        if v and "visto" not in v and base_lemma(lemma) == "vestir":
            return f"{lemma}: 1sg present '{v}' expected 'me visto' (e→i)"
    elif kind == "es-car-pret":
        v = g("1sg_pret")
        if v and not v.endswith("qué") and not v.endswith("que"):
            return f"{lemma}: ES -car 1sg preterite '{v}' should end -qué (busqué, not *buscé)"
    elif kind == "es-gar-pret":
        v = g("1sg_pret")
        if v and not (v.endswith("gué") or v.endswith("gue")):
            return f"{lemma}: ES -gar 1sg preterite '{v}' should end -gué (llegué)"
    elif kind == "es-ger-pres":
        v = g("1sg_pres")
        if v and not v.endswith("jo"):
            return f"{lemma}: ES -ger/-gir 1sg present '{v}' should end -jo (recojo, not *recogo)"
    elif kind == "pt-car-pret":
        v = g("1sg_pret")
        if v and not v.endswith("quei"):
            return f"{lemma}: PT -car 1sg preterite '{v}' should end -quei (busquei/troquei)"
    elif kind == "pt-gar-pret":
        v = g("1sg_pret")
        if v and not v.endswith("guei"):
            return f"{lemma}: PT -gar 1sg preterite '{v}' should end -guei (briguei/cheguei)"
    elif kind == "de-sein":
        v = g("perfect_aux")
        if v and v not in {"sein", "bin", "ist", "bist"}:
            return f"{lemma}: DE Perfekt auxiliary '{v}' should be sein (ich bin …), not haben"
    return None


def parse_verbs(args) -> list[dict]:
    verbs: list[dict] = []
    if args.json:
        try:
            data = json.loads(Path(args.json).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            sys.stderr.write(f"ERROR: cannot read --json {args.json}: {exc}\n")
            sys.exit(2)
        for item in data:
            verbs.append({"lemma": item["lemma"], "lang": item["lang"]})
    if args.verbs:
        for tok in args.verbs.split(","):
            tok = tok.strip()
            if not tok:
                continue
            if ":" not in tok:
                sys.stderr.write(f"ERROR: --verbs entry '{tok}' must be lemma:lang\n")
                sys.exit(2)
            lemma, lang = tok.rsplit(":", 1)
            verbs.append({"lemma": lemma.strip(), "lang": lang.strip()})
    for v in verbs:
        if v["lang"] not in LANGS:
            sys.stderr.write(f"ERROR: unknown lang '{v['lang']}' (use de|pt|es)\n")
            sys.exit(2)
    if not verbs:
        sys.stderr.write("ERROR: no verbs given (use --verbs or --json)\n")
        sys.exit(2)
    return verbs


def plan(verbs: list[dict]) -> dict:
    out = []
    for v in verbs:
        lemma, lang = v["lemma"], v["lang"]
        conj = CONJUGATORS[lang]
        url = conj["url"].format(lemma=base_lemma(lemma))
        ts = traps_for(lemma, lang)
        out.append({
            "lemma": lemma,
            "lang": lang,
            "conjugator": conj["name"],
            "url": url,
            "verify_cells": conj["cells"],
            "traps": [{"trap": t["trap"], "note": t["note"]} for t in ts],
        })
    return {"mode": "plan", "verbs": out}


def validate(verbs: list[dict], forms_path: str) -> tuple[dict, int]:
    try:
        supplied = json.loads(Path(forms_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"ERROR: cannot read --forms {forms_path}: {exc}\n")
        sys.exit(2)
    by_key = {(s["lemma"], s["lang"]): (s.get("forms") or {}) for s in supplied}

    results = []
    n_viol = 0
    for v in verbs:
        lemma, lang = v["lemma"], v["lang"]
        forms = by_key.get((lemma, lang), {})
        errs = []
        for t in traps_for(lemma, lang):
            pres_kind = t["_check"][0]
            extra_kind = t["_check"][2]
            for kind in (t["_check"][1], t["_check"][3]):
                if kind:
                    e = _violation(kind, lemma, forms)
                    if e:
                        errs.append(e)
        if not forms:
            errs.append(f"{lemma} ({lang}): no forms supplied to validate")
        n_viol += sum(1 for e in errs if "no forms supplied" not in e)
        results.append({"lemma": lemma, "lang": lang,
                        "ok": not any("no forms supplied" not in e for e in errs),
                        "issues": errs})
    return {"mode": "validate", "verbs": results, "violations": n_viol}, n_viol


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Plan/validate the learn-language verb conjugation self-check.")
    ap.add_argument("--verbs", default=None, help="lemma:lang,lemma:lang,… (lang=de|pt|es)")
    ap.add_argument("--json", default=None, help="JSON list of {lemma,lang}")
    ap.add_argument("--validate", action="store_true", help="check supplied forms vs trap rules")
    ap.add_argument("--forms", default=None, help="JSON of pulled forms (for --validate)")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args(argv)

    verbs = parse_verbs(args)
    indent = 2 if args.pretty else None

    if args.validate:
        if not args.forms:
            sys.stderr.write("ERROR: --validate requires --forms PATH\n")
            sys.exit(2)
        result, n_viol = validate(verbs, args.forms)
        print(json.dumps(result, ensure_ascii=False, indent=indent, sort_keys=True))
        return 1 if n_viol else 0

    print(json.dumps(plan(verbs), ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
