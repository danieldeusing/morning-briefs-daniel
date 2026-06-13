---
name: twiced-idea-builder
description: >
  Turn a one-line twiceD project hunch into a researched, market-grounded
  "Projekt-Ideen für twiceD" entry for the ai-usecases newsletter — the brief's
  signature closing section. Enforces the 4-block structure per idea (ELI5 + value
  / prototype-MVP plan / market landscape + the gap with NAMED competitors and
  sizing / small-team feasibility), runs each idea through the solo-or-tiny-team
  feasibility filter, and walks the per-idea competitor-fetch research checklist so
  every market claim ships with a source. Reach for it whenever you're writing or
  refreshing the projekt-ideen-twiced section, turning a raw pitch ("a document
  order agent for the Mittelstand", "an AI-Act audit service") into a real
  proposal, or you catch yourself about to assert a market fact ("Rossum writes to
  the ERP", "the IDP market is $14B") from memory instead of fetching it. Triggers:
  "deepen the twiceD ideas", "write the projekt-ideen section", "turn this pitch
  into a proposal", "what's the market for this twiceD idea", "build the twiceD
  ideas block". ai-usecases-specific — not for other newsletters.
---

# twiced-idea-builder

## Why this exists

The closing section of the ai-usecases brief is **"Projekt-Ideen für twiceD"** —
B2B opportunities Daniel could actually pursue with twiceD (his solo software
shop, augmentable with AI + occasional contractors). It is the part of the brief
that does real work for him: it's the difference between "here's some AI news" and
"here's a thing you could build and sell next month."

For a while these were one-line pitches: a pattern, a "twiceD-fit", a lead hint.
That reads as a brainstorm, not a plan. The fix Daniel asked for: each idea must be
a **researched proposal** — it must say *what it is in plain words and why it
matters*, *how you'd build a first version*, *who already does this and where the
gap is* (with named competitors and real numbers), and *whether a solo-plus-AI
shop can actually own it long-term*. The research is the heavy part and the part
most likely to be skipped under time pressure or faked from memory.

This skill pins that structure down so the quality of the section doesn't depend on
remembering all four blocks, the feasibility lens, and the "every market claim gets
a source" rule every single morning. It is **process guidance**, not a code
transform — the value is in asking the right questions in the right order and
producing the right HTML.

## The contract: every `.idee` has four blocks, in this order

Write each idea as one `.idee` card inside the `projekt-ideen-twiced` component
(see "Output" below). Lead the card with a short `<h3>` title, then exactly these
four bold-label blocks, separated by `<br>`:

1. **ELI5 & Wert** — In plain language: what is this, and *why should twiceD care*?
   Name the concrete value to the customer — money saved, time saved, risk avoided
   — not "leverages AI". One sentence of analogy is fine if the concept is fuzzy.
   If you can't say what problem it solves in two sentences, the idea isn't ready.

2. **Prototyp (V0)** — How would you build the smallest thing that proves it works?
   3–5 concrete steps to an MVP. Say what's *in* the V0 and what's deliberately
   left out. **Name the existing building blocks** (an API, an open-source library,
   a model, a framework) so it's clear you're not reinventing the wheel — twiceD's
   edge is assembly + fit, not building primitives.

3. **Markt & Lücke** — *The heaviest block; weight your effort here.* What already
   exists, named concretely (vendors, tools, platforms) **with a source per claim**?
   What do they do badly or leave out? *Why is that the opening for twiceD* — the
   gap the big players won't fill (too generic, too expensive, no DE-Mittelstand
   focus, no sovereignty/on-prem option, no hands-on delivery)? A market claim
   without a citation is a guess; see the research checklist below.

4. **Machbarkeit (Solo + AI)** — twiceD is **Daniel solo, plus AI, plus the
   occasional contractor.** It can scale, but not to big-corp scale. Answer
   honestly: what's the maintenance burden? Roughly how many hours/week to run and
   to scale? Can a tiny team *own this long-term*, or would it need a 10-person
   team (if so, it fails the filter — see below)? Where sovereignty is the wedge,
   name the on-prem / open-model variant.

Two deeply-researched ideas beat three shallow ones. On a quiet news day, one
strong idea is fine. 1–3 ideas total.

## The solo-or-tiny-team feasibility filter

Run every idea through this before it earns a spot. twiceD's constraint is the
whole point of the section — an idea that's brilliant but needs a standing team is
the wrong idea *for Daniel*, however good it'd be for someone else.

- **Build:** can a V0 be stood up by one person (+AI, +maybe one contractor) in
  weeks, not quarters? If it needs a team to even reach a prototype → cut or
  re-scope.
- **Maintain:** what does week-N look like after launch? Advisory/one-shot work
  (e.g. an audit) has ~zero ongoing maintenance and scores high. A hosted service
  (model ops, GPU, monitoring) has real ongoing load — say so honestly; it can
  still qualify if the load is bounded and one person can carry it.
- **Scale path:** scaling should be "add a contractor per client", not "hire a
  department". If the only way to grow is headcount twiceD can't sustain, it's a
  poor fit.
- **Verdict:** state it plainly — High / Medium / Low feasibility — and *say why*.
  Don't hide a hard maintenance story behind enthusiasm; the honesty is what makes
  the section trustworthy to Daniel.

If an idea fails the filter, either re-scope it until a tiny team can own it (often
by narrowing to advisory or a single bounded workflow) or drop it.

## Per-idea competitor-fetch research checklist

Block 3 is only as good as the research behind it. For each idea, before writing,
walk this checklist — and follow the sourcing hierarchy from
`docs/CROSS_CUTTING.md` § 0 (primary/official sources first, then established
trade/news media, blogs/aggregators only as a last step and never as the sole
source for a number).

1. **Who already does this?** Search for the named incumbents — the platform
   vendors, the SaaS tools, the consultancies. Get *specific names*, not "various
   tools". (Example: for document-order automation → Rossum, ABBYY, Google Document
   AI, AWS Textract, LlamaIndex/LlamaParse.)
2. **How big / how fast?** Find a market-size or growth figure with a date and a
   source (e.g. "IDP ≈ $14B in 2026, ~26% CAGR"). One sourced number beats three
   vague adjectives. If you can't source it, don't state it.
3. **What do they do badly / leave out?** Identify the concrete shortcoming that
   creates room — usually "horizontal platform, customer must assemble it
   themselves", "no on-prem/sovereignty story", "enterprise-priced", "no German
   Mittelstand focus", "self-service not hands-on".
4. **Why is that twiceD's gap?** Tie the shortcoming to twiceD's actual edge:
   hands-on delivery, DE contract language + GDPR/UrhG reflex, sovereignty/on-prem
   via open models, willingness to fit one concrete workflow.
5. **Capture sources as you go.** Every name and number gets a URL you'll drop into
   the card's `.src` block. If a fetch fails, fall back per the ladder — do not
   fabricate. The `fetch-with-fallback` skill is the right tool when a source 403s
   or a page is JS-only.

When several ideas need parallel research, dispatch one sub-agent per idea
(per `docs/CROSS_CUTTING.md` § 1) rather than running all searches yourself.

## Output — HTML using the existing component

The section is the `projekt-ideen-twiced` component from `docs/COMPONENTS.md`. It
carries no new CSS/JS — it's `.idee` divs with bold-label blocks and inline `.src`
links, exactly like the rest of the brief. Drop it in as the **last** body section
(after the body-grid), before the voice-summary.

Per-language label set (translate the bold labels with the rest of the brief; keep
canonical proper nouns and source URLs unchanged):

| block | de | en | pt | es |
|---|---|---|---|---|
| 1 | `ELI5 &amp; Wert` | `ELI5 &amp; value` | `ELI5 &amp; valor` | `ELI5 y valor` |
| 2 | `Prototyp` | `Prototype` | `Protótipo` | `Prototipo` |
| 3 | `Markt &amp; Lücke` | `Market &amp; gap` | `Mercado &amp; lacuna` | `Mercado y brecha` |
| 4 | `Machbarkeit (Solo + AI)` | `Feasibility (solo + AI)` | `Viabilidade (solo + IA)` | `Viabilidad (solo + IA)` |

Section byline (DE): `Recherchierte Vorschläge — mit Markt-Lücke und ehrlicher Solo-Machbarkeit`.

### Card template (DE — copy, fill, translate)

```html
<div class="idee">
  <h3>{{N}} · {{Kurztitel der Idee}}</h3>
  <strong>ELI5 &amp; Wert:</strong> {{Was ist das, in einfachen Worten. Welches
  konkrete Problem löst es — gespartes Geld/Zeit, vermiedenes Risiko. Eine
  Analogie wenn nötig.}}<br>
  <strong>Prototyp (V0):</strong> (1) {{Schritt}} (2) {{Schritt}} (3) {{Schritt}}
  (4) {{Schritt}}. MVP bewusst eng: {{was drin / was bewusst draußen}}. Bestehende
  Bausteine: {{API/Open-Source/Modell}}.<br>
  <strong>Markt &amp; Lücke:</strong> {{Was es schon gibt — benannte Anbieter +
  Marktgröße mit Quelle}}.<sup>[N]</sup> {{Was die schlecht machen / auslassen}}.
  Lücke für twiceD: {{warum genau das die Chance ist}}.<br>
  <strong>Machbarkeit (Solo + AI):</strong> {{Hoch/Mittel/Niedrig}} — {{V0-Aufwand
  solo, Wartungslast, Stunden/Woche, Skalierung via Contractor. Ehrlich.}}
  <span class="src"><a href="{{url1}}">{{domain1}}</a> · <a href="{{url2}}">{{domain2}}</a></span>
</div>
```

The full section wrapper:

```html
<section class="twiced-ideen">
  <h2>Projekt-Ideen für twiceD</h2>
  <p class="byline">Recherchierte Vorschläge — mit Markt-Lücke und ehrlicher Solo-Machbarkeit</p>
  <!-- 1–3 .idee cards -->
</section>
```

### Worked example (real, from the 2026-05-20 brief)

A one-line pitch — *"AI document order agent for the Mittelstand"* — becomes:

```html
<div class="idee">
  <h3>1 · Dokumenten-Order-Agent für den Mittelstand</h3>
  <strong>ELI5 &amp; Wert:</strong> Bestellungen, Reklamationen und Lieferavise
  kommen bei vielen Mittelständlern als PDF, E-Mail oder Fax rein und werden von
  Hand ins ERP getippt. Ein „Dokumenten-Agent" liest diese unstrukturierten
  Eingänge, prüft sie und legt sie als saubere Order an. Wert: Levi's drückte genau
  diesen Prozess von 2–5 Tagen auf 20–30 Minuten — gespart wird teure
  Sachbearbeiter-Zeit und die Fehlerquote beim Abtippen.<br>
  <strong>Prototyp (V0):</strong> (1) Ein realer Dokumenten-Stapel des Kunden als
  Testset. (2) Extraktion über ein bestehendes IDP-Modell (Layout + Felder), nicht
  selbst gebaut. (3) Validierungs-Logik gegen Stammdaten. (4) Schreib-Adapter ins
  Ziel-ERP für eine Belegart. MVP eng: ein Dokumenttyp, ein Kunde, Mensch bestätigt
  vor dem Buchen.<br>
  <strong>Markt &amp; Lücke:</strong> Der IDP-Markt ist groß (≈ 14 Mrd. $ 2026,
  CAGR ~26 %) mit reifen Anbietern — Rossum, ABBYY, Google Document AI, LlamaParse.<sup>[10]</sup>
  Die sind aber horizontale Plattformen: der Kunde steckt Workflow, Anbindung und
  Validierung selbst zusammen. Lücke: der letzte Meter — Einpassung in einen
  konkreten DE-Mittelstand-Prozess, on-prem für sensible Daten, ohne SaaS-Abo pro
  Seite.<br>
  <strong>Machbarkeit (Solo + AI):</strong> Hoch. Das schwere Modell kommt von der
  Plattform; twiceD baut Adapter + Validierung + Betrieb. V0 in 4–6 Wochen solo,
  Roll-out mit 1 Contractor. Wartung gering, solange der Scope eng bleibt.
  <span class="src"><a href="https://rossum.ai/">rossum.ai</a> · <a href="https://www.llamaindex.ai/insights/best-document-processing-software">llamaindex.ai</a></span>
</div>
```

Note how each of the four blocks earns its place: the value is a concrete
before/after (days → minutes), the prototype names a real building block (an IDP
model) instead of "build OCR", the market block carries two sources and a sized
gap, and the feasibility verdict is "High" *with the reason* (heavy lifting is
bought, not built) — not just a thumbs-up.

## Self-check before you ship the section

- Every `.idee` has all four labelled blocks, in order, with an `<h3>` title.
- Every market claim in block 3 has a source; the card carries a `.src` block.
- Every idea has a stated feasibility verdict (High/Medium/Low) **with a reason**,
  and survives the solo-or-tiny-team filter.
- No idea needs a standing team to build *or* maintain.
- Labels translated per the table for en/pt/es; proper nouns + URLs unchanged.
- The section is the last body section, before the voice-summary.
- The brief still fits its word ceiling after adding the section — research weight
  is fine, but trim elsewhere if needed (DE is canonical; translate after trimming,
  per `docs/FORMAT.md`).
