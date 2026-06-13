---
name: sports-time-trizone
description: >
  Convert one event/kickoff/session time into the multiple timezones the
  football and motorsport Morning Briefs require — with daylight-saving computed
  from the real tz database, never hand-guessed. Football needs MEZ/MESZ + BRT;
  motorsport needs track-local + BRT + MESZ/CEST. Brazil has no DST (BRT is
  UTC-3 all year) while Europe shifts, so the BRT↔Europe gap is 4h in winter and
  5h in summer — easy to get wrong by an hour if you compute it in your head.
  Use this WHENEVER you write a kickoff, race, practice, qualifying, sprint, or
  any dated event time in the football or motorsport briefs, in any of the four
  languages. Reach for it the moment you're about to type a time with a zone
  label — that's the moment a hand-converted offset goes wrong across a DST
  boundary. Triggers: "convert this kickoff to BRT", "what's 21:00 MEZ in
  Brasília", "trizone", "dual-timezone kickoff", "F1 session times in three
  zones", "is this MEZ or MESZ for that date", "Bundesliga time in Daniel's
  zone", "Imola race start BRT". Football + motorsport only — pairs with the
  football.py / motorsport.py brief-gate modules that flag an unpaired EU time.
---

# sports-time-trizone

## Why this exists

Daniel reads in Ribeirão Claro/PR — **BRT, UTC-3, and Brazil keeps no daylight
saving**, so BRT is -3 every day of the year. The competitions he follows do
shift: Europe runs **MEZ/CET (UTC+1) in winter and MESZ/CEST (UTC+2) in
summer**, and a motorsport round can start in any zone on earth. So the
Brazil↔Europe gap is **4 hours in winter, 5 hours in summer**, and the exact
day a fixture falls on decides which — the last Sunday of March and October flip
Europe but not Brazil.

The recurring brief mistake is exactly here: a bare "21:00 MEZ" with no Brazil
partner, or an offset computed in someone's head that lands an hour off because
the date sits on the wrong side of a DST switch. The football and motorsport
SKILLs both say *"compute concretely; never guess"* — this skill is how. It
converts via the real IANA timezone database, so the season's offset for that
specific date is correct by construction.

The football.py and motorsport.py **brief-gate modules** flag an event time that
carries a European zone with no BRT partner. Using this skill is how you satisfy
that gate without thinking about offsets at all.

## The converter

`scripts/trizone.py` (stdlib only — uses Python's `zoneinfo`, no install). You
give it the wall-clock time, the date it falls on, and the zone that time is
**stated in**; it returns all the zones, DST already resolved:

```bash
# Football — a Bundesliga kickoff stated in German time:
python3 .claude/skills/sports-time-trizone/scripts/trizone.py \
    --time 20:30 --date 2026-05-23 --in-zone berlin
```

prints (among the JSON):

```
"football_string":   "20:30 MESZ / 15:30 BRT"
```

```bash
# Motorsport — a race stated in the venue's local time (Miami, US Eastern):
python3 .claude/skills/sports-time-trizone/scripts/trizone.py \
    --time 16:00 --date 2026-05-03 --in-zone et --track-zone et
```

```
"motorsport_string": "16:00 EDT / 17:00 BRT / 22:00 CEST"
```

### Which string to paste

- **Football** → use `football_string`: two zones, **MEZ/MESZ + BRT**, in the
  brief's canonical order (European zone first, Daniel's zone second).
- **Motorsport** → use `motorsport_string`: three zones, **track-local + BRT +
  MESZ/CEST**. If the round is *in Europe* (Imola, Monza, Spielberg…), the track
  zone and the Europe zone are the same, so the string repeats the European time
  at both ends — that's correct but redundant; for a European round just use
  `football_string` (it already shows the European time + BRT), or keep the
  three-zone form, your call. The three-zone form earns its keep for
  non-European venues (the Americas, Asia, the Gulf, Australia).

The JSON also carries `brt`, `europe` (with both `label`=MEZ/MESZ and
`label_en`=CET/CEST), and `track`, if you want to assemble a custom phrasing.

## Naming a zone

`--in-zone` / `--track-zone` accept either a full **IANA name**
(`Europe/Berlin`, `America/Sao_Paulo`, `Asia/Bahrain`) or a short **alias** the
script knows. Handy aliases:

| alias | zone | | alias | zone |
|-------|------|-|-------|------|
| `brt`, `brasilia` | Brazil (UTC-3) | | `et`, `miami` | US Eastern |
| `berlin`, `cet`, `mez` | Europe (Berlin) | | `austin` | US Central |
| `uk`, `london` | UK | | `lasvegas` | US Pacific |
| `bahrain`, `qatar` | Gulf | | `suzuka`, `japan` | Japan |
| `interlagos`, `brazil` | São Paulo GP | | `melbourne` | Australia |
| `imola`, `monza`, `spa` | Europe (track) | | `mexicocity` | Mexico |

Unknown zone or a malformed time/date → exit 2 with a clear error. Treat exit 2
as "fix the inputs" — never as licence to hand-write the time.

## What this skill is NOT

It converts **one stated time** you already know. It does not look up when a
fixture kicks off — that's a research/fetch step (see `fetch-with-fallback` for
standings, and the brief's normal sourcing for fixture times). Give it the time
from the source; it gives you back the zones, correct to the day.

## Worked DST check (why the date matters)

Same 15:30 Berlin kickoff, two dates:
- `--date 2026-05-23` (summer) → `15:30 MESZ / 10:30 BRT` — 5h gap.
- `--date 2026-01-17` (winter) → `15:30 MEZ / 11:30 BRT` — 4h gap.

The BRT clock differs by an hour between the two **for the same German time** —
precisely the error a hand-conversion makes, and precisely what the tz database
gets right.
