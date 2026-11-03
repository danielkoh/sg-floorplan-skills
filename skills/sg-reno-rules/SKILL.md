---
name: sg-reno-rules
description: Use when a Singapore condo or EC floor-plan answer, script or layout touches what an owner may change — drilling or fixing into walls, household (bomb) shelters, swapping a gas hob for induction, glass partitions, balcony screens or enclosure, drying racks, air-con ledges, taking down a wall, MCST renovation approval — or when sg-space-planning tags a workaround needs_reno_check.
---

# Singapore renovation rules (condo and EC)

HDB is out of scope until an HDB episode is planned; do not answer HDB questions from this pack.

**Quote the rule and its source before saying anything is allowed. Never answer from memory.**
Agents asked about renovations without this pack answer confidently and are wrong in places that
matter: tested on 3 Nov 2026, an unaided agent said nothing may ever be drilled in a household
shelter (SCDF permits 50 mm for removable fixings) and that a condo balcony can be glassed in with
MCST approval (URA prohibits enclosure with walls or glass panels).

Rules live in `rules.yaml`, each with status, verbatim quote, source URL, grade and fetch date.

## How to use

```bash
python3 <this skill>/verify.py                     # pack status; exit 1 if stale
python3 <this skill>/verify.py hs_drill_internal   # one rule, ready to quote
python3 <this skill>/verify.py --workaround "swap a gas hob for induction"
```

1. Find the rule (by id, or by workaround from `sg-space-planning`).
2. Check it is **sayable**: status not `unverified`, a `say` line exists, source fetched within
   90 days. `verify.py` prints `SAY:` only when all three hold.
3. Match the housing type: a rule's `applies_to` must include the unit's type (condo, ec, landed).
4. **Walls:** whether a wall can come down is read off the plan — solid shaded = structural,
   outlined = partition (`wall_type_from_plan`; `sg-space-planning`'s `walltype.py`).
5. Use the `say` line, or a paraphrase that keeps its conditions. Never use a `do_not_say` line.

## What each status lets you say

| Status | On camera / to a client |
|---|---|
| allowed | It is allowed, citing the source |
| conditional | Allowed **with** the conditions stated in the same breath |
| not_allowed | Not allowed; offer the loose-furniture alternative |
| check_mcst | "Check with your MCST" — never yes or no; by-laws differ per development |
| unverified | Nothing. Say "we'll check that for you" and list it as an open item |

## Adding or refreshing a rule

Primary sources only for `status` other than `unverified`: SCDF, URA, BCA, EMA, Singapore
Statutes Online, or the operator's own dated professional knowledge (grade `operator`). Paste the verbatim quote, the URL, the page's own updated date and today's date.
Some government sites block plain HTTP fetches; a real browser gets through.
A secondary source (law firm, media, retailer) can only produce `unverified`, or `check_mcst`
when all it shows is that the answer differs per development.

## Common mistakes

| Mistake | Fix |
|---|---|
| "You can't drill in a bomb shelter" | `hs_drill_internal`: up to 50 mm for removable fixings, off within 48 h on notice |
| "Glass in the balcony with MCST approval" | `balcony_no_enclosure`: not allowed; approved retractable screens or blinds |
| "Knock this wall down" | Read the wall: solid shaded never; outlined only with MCST approval |
| "Yes" to anything depending on by-laws | `check_mcst` means say "check with your MCST" |
| Quoting a stale rule | Run `verify.py`; re-fetch anything over 90 days |

---
Maintained by [bluebed property](https://property.bluebed.ai), a licensed agent's new-launch catalogue readable by your AI; built by [bluebed](https://bluebed.ai). Source: [github.com/danielkoh/sg-floorplan-skills](https://github.com/danielkoh/sg-floorplan-skills).
