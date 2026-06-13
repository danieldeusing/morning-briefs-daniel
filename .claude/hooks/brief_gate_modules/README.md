# Per-category gate modules — the interface (#58 owners read this)

The brief-gate hook (`../brief_gate.py`) runs SHARED structural checks on every
brief, then — if a module exists for the brief's category — runs that module's
category-specific checks too. This file is the **contract** each category owner
implements in task #58.

## The contract

Create `.claude/hooks/brief_gate_modules/<category>.py` where `<category>` is the
exact folder name (`economy`, `software`, `ai-dev`, `ai-usecases`, `football`,
`family`, `jobs`, `learn-language`, `motorsport`, `stocks-crypto`).

The module MUST define one function:

```python
def check_brief(ctx) -> list[Finding]:
    ...
```

- It is called once per edited brief of that category, in any of the 4 languages.
- It returns a list of `Finding` (empty list = brief passes your category checks).
- A missing module, a module with no `check_brief`, or one that raises is
  non-fatal — the framework surfaces that as a warning and never blocks the edit.

## `ctx` — what you get (read-only)

`ctx` is a `BriefContext` with:

| field        | type | meaning |
|--------------|------|---------|
| `ctx.path`     | `Path` | absolute path to the edited file |
| `ctx.category` | `str`  | e.g. `"economy"` |
| `ctx.lang`     | `str`  | folder lang: `de` \| `en` \| `pt` \| `es` |
| `ctx.date`     | `str`  | `YYYY-MM-DD` |
| `ctx.html`     | `str`  | full file text |
| `ctx.body`     | `str`  | text from `<body …>` onward |
| `ctx.sibling(lang)` | `Path` | path to the same date's file in another language folder |

## `Finding` — what you return

Import it from the framework (modules are loaded next to `brief_gate.py`):

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding
```

`Finding(check, message, level="warn")`:
- `check` — short stable id, e.g. `"missing-disclaimer"`. Shows in the report.
- `message` — human-readable; tell the agent exactly what to fix.
- `level` — `"warn"` (default, non-blocking) or `"block"`.

You may also return plain dicts `{"check": ..., "message": ..., "level": ...}`;
the framework coerces them to `Finding`.

## Policy: warn vs block

**Default to `warn`.** Warnings inform; they never stop the edit. Reserve
`level="block"` for issues that are *liability- or money-critical* — a brief that
ships with one is materially wrong, not merely imperfect. The two blocking checks
mandated for Phase 0 (already implemented here as reference modules):

- **stocks-crypto** → missing risk/disclaimer text (`stocks-crypto.py`).
- **economy** → fabricated or undated FX series in a chart data block (`economy.py`).

Everything else (tone, depth, source count, length) is a warning.

## Language awareness

`check_brief` runs for all four languages. If your check matches visible text
(e.g. a disclaimer phrase), match a **set** of per-language variants keyed off
`ctx.lang`, not a single German string — otherwise you'll false-positive on the
EN/PT/ES files. The reference modules show the pattern.

## Minimal example

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from brief_gate import Finding

def check_brief(ctx):
    out = []
    if "<table" not in ctx.body.lower():           # category needs a standings table
        out.append(Finding("missing-standings",
                            "Football brief has no standings <table>.", level="warn"))
    return out
```

## Testing your module

```bash
echo '{"tool_input":{"file_path":"'"$PWD"'/public/<cat>/de/<date>.html"}}' \
  | python3 .claude/hooks/brief_gate.py
```

Clean brief → no output. A finding → JSON with a `systemMessage` (warn) or
`decision:block` + `reason` (block).
