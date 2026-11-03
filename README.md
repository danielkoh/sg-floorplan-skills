# sg-floorplan-skills

Open-source skills that let Claude and other AI assistants **read a Singapore condo floor plan
the way a careful agent would**: measure it, find the layout issues that put buyers off, lay out
the rooms for a real household with a geometry check, and say what an owner may change — each
rule quoted from its source.

> **Not legal, renovation or property advice.** These skills present measurements, checks and
> quoted rules. Renovation rules differ per development: always confirm with your MCST, the
> developer's documents and the relevant authority before you buy, drill or hack anything.

## Skills

| Skill | What it does |
|---|---|
| `sg-floorplan-analysis` | Reads a developer floor plan into a fixed, comparable schema: area accounting (strata, balcony, AC ledge, voids), layout, bedrooms, orientation per stack, feng shui as resale liquidity. `measure.py` sizes rooms exactly from vector PDFs. |
| `sg-space-planning` | Finds buyer-deterring layout issues (`issues.py`), lays rooms out for a household and **proves the layout fits** (`fit.py`: overlaps, door swings, use zones, walkways, wall beds open and closed), and reads whether a wall is structural off the plan image (`walltype.py`). Sizes and clearances in `standards.yaml`, each with a source and grade. |
| `sg-reno-rules` | What a condo or EC owner may drill, fix, swap or enclose — household shelters (SCDF), strata by-laws, balcony enclosure (URA), gas works (EMA) — each rule with a verbatim quote, URL, grade and fetch date. `verify.py` prints a sayable line only for verified, fresh rules. |

The three work together: an issue found by `sg-space-planning` that needs a renovation is checked
against `sg-reno-rules` before anyone says it can be done.

## Install

Claude Code plugin (one step, Claude Code 2.1.275+):

```
/plugin install sg-floorplan-skills --marketplace danielkoh/sg-floorplan-skills
```

Older Claude Code: `/plugin marketplace add danielkoh/sg-floorplan-skills`, then
`/plugin install sg-floorplan-skills`.

Any agent, with the [skills CLI](https://skills.sh):

```
npx skills add danielkoh/sg-floorplan-skills
```

Or copy any `skills/<name>/` folder into your agent's skills directory. Python 3.10+ with
`pyyaml` and `pillow` (`pymupdf` for `measure.py`).

## Try it

```bash
python3 skills/sg-space-planning/issues.py example-residences --data-dir tests/fixtures --type 2A
python3 skills/sg-space-planning/fit.py skills/sg-space-planning/examples/example-2br-bed2-wallbed-FAIL.json
python3 skills/sg-reno-rules/verify.py --workaround "glass in the balcony"
```

## What it runs

Only the bundled Python scripts, on your machine, when your agent calls them: `measure.py`,
`fit.py`, `issues.py`, `walltype.py` and `verify.py`. They read the files you point them at
(a plan PDF or image, a layout JSON, your checklist folder) and print a report. Nothing is sent
or fetched over the network, there are no hooks or MCP servers, and nothing is installed. The
source URLs in `rules.yaml` are references for a person to open; the scripts never request them.

## How the rules stay honest

- Every renovation rule carries its source, grade (`official`, `operator`, `secondary`) and the
  date it was fetched. Secondary sources can never make a rule sayable.
- Rules older than 90 days stop printing a sayable line, and CI turns red, until re-fetched.
- Layouts are claims; `fit.py` checks them, and a failed layout is kept as evidence, never shown.

## Contributing

Pull requests welcome, especially rules. A new or changed rule needs the verbatim quote, the
primary-source URL (SCDF, URA, BCA, EMA, Singapore Statutes Online), the page's own updated date
and the date you fetched it. Run `python3 -m pytest -q` before opening the PR.

## About

Built and used daily by **[bluebed property](https://property.bluebed.ai)** — a licensed agent's
new-launch catalogue, readable by your AI. Floor plans, measured MRT and school distances, and the
rules behind every figure. The engineering behind it is by **[bluebed](https://bluebed.ai)**.

- Related: [property-bluebed-mcp](https://github.com/danielkoh/property-bluebed-mcp), the MCP server that lets your assistant search the same reviewed floor plans; connect it at [property.bluebed.ai/connect](https://property.bluebed.ai/connect).
- Source: [github.com/danielkoh/sg-floorplan-skills](https://github.com/danielkoh/sg-floorplan-skills)
- Licence: MIT. The evidence rules in `sg-space-planning` adapt the method of pascalorg/editor's
  `furniture-fit` skill (MIT).
