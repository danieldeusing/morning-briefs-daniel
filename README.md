# Morning Briefs

An automated daily newsletter generator producing 7 category newsletters in 4 languages (DE/EN/PT/ES), served as a static site at **https://briefs.danieldeusing.de**.

![A 30-second tour: the dashboard, then the newest English edition of each category](video/tour.gif)

## How it works

A single Claude Code scheduled task (the coordinator) fires each morning (~06:00)
and dispatches per-phase subagents, each on the cheapest model that does its job
well — research is fetch-heavy and cheap, writing is where the reasoning (and the
strong model) goes, translation is mechanical:

| Phase | Agent | Model | Output |
|---|---|---|---|
| Research | `brief-researcher` | Sonnet | Sourced-fact dossier |
| Write DE (canonical) | `brief-writer` | Opus 4.8 (complex categories) / 4.7 (rest) | `public/<cat>/de/<date>.html` |
| Translate EN/PT/ES | `brief-translator` | Sonnet | `public/<cat>/{en,pt,es}/<date>.html` |
| Fact-check + fix | `brief-fact-checker` | Sonnet | Structured report → fix loop (max 2 rounds) |
| Jobs pre-research | `jobs-aggregator` | Sonnet | Listings JSON |
| Dashboard | `tools/build_manifest.py` | — | Rewrites `window.__MANIFESTS` in `index.html` |

The German file is canonical (all research + judgement happens there); the other
three languages are translations of it. Categories (processed in batches of 3):
economy, software, ai-dev, ai-usecases, family, jobs, learn-language.

## Repo layout

```
public/         Static site (served directly; per-category de/en/pt/es subfolders)
docs/           Editorial specs — categories/<cat>.md drives what each brief covers
tools/          Build scripts (build_manifest.py)
.claude/        Agents, skills, and hooks that drive generation (not web-reachable)
video/          Remotion source of the tour above (npm run capture && npm run render && npm run gif)
```

## Running it

Generation runs as a **local Claude Code scheduled task** stored outside this repo at `~/.claude/scheduled-tasks/morning-briefs-daniel---morning-brief-all/`. A clone of this repo gets the static site and the editorial specs, but not the runnable task.

## License

[MIT](LICENSE).
