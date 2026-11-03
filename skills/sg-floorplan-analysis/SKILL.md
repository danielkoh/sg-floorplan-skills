---
name: sg-floorplan-analysis
description: Use when analysing a Singapore condo, HDB or landed floorplan image or PDF — reading a unit layout, judging whether a plan is good or bad, comparing layouts, assessing 户型, or turning a floorplan into social content in English or Mandarin.
---

# Singapore floorplan analysis

Reads a floorplan and produces a comparable, sourced judgement of it — area accounting,
layout, resale liquidity — in a fixed schema, so twenty units analysed over three months can
be set beside each other.

**Core principle: separate what you measured from what you inferred from what you cannot see.**
An analysis that blurs the three reads as authority and is worthless the first time it is wrong
in public.

## When to use

- A floorplan image or PDF needs judging — "is this a good layout", "what's wrong with this unit"
- Producing floorplan content, in either language
- Comparing two units
- Someone asks about 户型, AC ledge, PES, bay windows, efficiency, dumbbell layouts

**Not for:** interior furnishing or furniture placement; property valuation; anything requiring
duty, ABSD, LTV or TDSR figures — those come from `sgprop`, never from reading a plan.

## The rubric is a file, not this document

`rubric.yaml` holds every criterion, band and threshold. **Read it at the start of each analysis
and work it in order.** It is versioned so criteria can change without silently changing what
past analyses meant.

Do not analyse from memory of this skill. The rubric is the checklist; this file is only how to
apply it.

## Ask for the whole set, not one page

A developer floorplan is normally **two or more sheets**: the unit plan, and a legend sheet
carrying the scale bar, the abbreviation key (F, WD, P, DB, ST, IH) and the **key plan** with the
north arrow and the shaded stack.

**Without the second sheet you cannot measure rooms and cannot state orientation.** If only the
unit plan is supplied, ask for the legend/key-plan page before analysing — it changes findings
from `inferred` to `measured`, which is the difference between an opinion and a fact.

**Orientation is a property of the stack, never of the unit type.** One type is built into many
stacks across several blocks facing different ways. "This unit gets afternoon sun" is wrong by
construction unless a stack is named.

## Measure it if you can — `measure.py`

Developer floorplans are usually **vector PDFs, not scans**. When they are, room sizes are exact
and every dimension moves from `inferred` to `measured`. Always try this before eyeballing.

```bash
python3 measure.py plan.pdf                # auto-detect scale, size every labelled room
python3 measure.py plan.pdf --scale-only   # check the scale bar was found correctly
python3 measure.py plan.pdf --ppm 18.84    # force points-per-metre if detection is wrong
```

It reads the scale bar's tick pitch, then bounds each room label with its nearest wall lines.
On a strata-terrace sheet it returned 18.85 pt/m and matched hand measurement to within
0.1 sqm across every room.

**Check the scale first, every time.** `--scale-only` costs one second and a wrong scale makes
every number wrong in the same direction, which is the hardest error to notice. Sanity-check it
against something known: a carpark bay is about 2.4 m wide, a door leaf 0.9 m.

**A label inside an open-plan zone reports the whole zone, not a room.** Anything implausibly
deep — a bedroom reading 15 m — has been bounded by the outer walls rather than its partitions.
Measure those by hand.

**No geometry returned means it is a scan.** Fall back to scaling off a 0.9 m door leaf and mark
everything `inferred`. Say which in the output.

## Workflow

1. **Read `rubric.yaml`.**
2. **Run `measure.py`, and check the scale bar and key plan** — they set the confidence marks for
   everything that follows.
3. **Extract the stated numbers** — strata area, balcony area, unit type, block and stack. Quote
   them as printed. If the plan does not state a number, it is `unknown`, not an estimate.
4. **Compute the area ratios** the rubric defines. Show the arithmetic.
5. **Work `layout`, then `feng_shui`, then `resale`**, in that order. Resale last, because it
   depends on everything above.
6. **Mark every finding** with one of three confidence levels — see below.
7. **Emit the schema.**

## Confidence marking is mandatory

Every finding carries exactly one:

| Mark | Meaning |
|---|---|
| `measured` | Read directly off the plan, or computed from numbers printed on it |
| `inferred` | A judgement from the drawing — proportions, likely furniture fit, sightlines |
| `unavailable` | Cannot be determined from this image; says what would be needed |

**`unavailable` is a real answer and must be used** — but only after checking for the legend and
key-plan sheet. With the full set, orientation, external context and room dimensions are all
`measured`. Without it they are `unavailable`, and the correct move is to ask for the sheet, not
to guess.

Floor level, actual view, and construction noise stay `unavailable` regardless — those need the
stack chart, a site visit, or URA plans. Guessing them is the fastest way to be confidently wrong
in front of a buyer.

## How findings are phrased

Every floorplan is somebody's home, and often somebody's future listing. The analysis is honest
about weaknesses and never insulting about them.

**Each finding takes this shape, in this order:**

1. **What is there** — the measured fact, plainly.
2. **Who it suits** — the buyer or household this serves well.
3. **Who should look elsewhere** — stated as fit, not as fault.

**Open the analysis with the strongest genuine feature the plan has.** Every plan has one; find it
before listing anything else. A plan with no redeeming feature means you have not looked hard
enough, not that the plan is worthless.

Worked contrast, same fact:

> ✗ "The kitchen is badly designed — no ventilation, terrible for a small unit."
>
> ✓ "The kitchen is open to the dining area with no external window, which keeps the space feeling
> larger and suits light cooking. If you wok daily, this is the one to check in person — smell
> carries and it can't be closed off later."

Both say the kitchen cannot vent. The second is more useful, survives being read by the owner,
and still gives the viewer a reason to act.

**A trade-off is the default frame.** Almost every "flaw" is a deliberate design decision that
serves someone: a large balcony costs internal area and is loved by people who use it; a dumbbell
plan buys efficiency and costs acoustic privacy. Report both sides and let the reader place
themselves.

**Say what it would take to fix**, where anything can be. A named remedy is generous and useful;
a flaw with no path is just criticism.

For anything structural and unfixable — expressway frontage, a void, a missing corner — state it
once, factually, without repeating or emphasising it. It goes in `RESALE` as a pool-narrowing
fact, not in the verdict as a judgement on the developer.

**Never characterise the project, the developer or the architect.** The subject is always the fit
between this layout and a particular household.

## Output schema

Fixed. Do not add or reorder sections; comparability across posts is the entire point.

```
UNIT          <project, type, block/stack if shown>
STRENGTHS     <the two or three things this plan genuinely does well — first, always>
DISCLAIMER    <the area small-print, quoted verbatim — it governs everything below>
AREA          strata; balcony (sqm, % of strata); AC ledge (strata|non-strata);
              void area (sqm, % of strata); dead area
              <each with mark>
ROOMS         per bedroom: largest bed that fits + what is left over
              dining: largest table that fits
              <each with mark, using the reference dimensions in rubric.yaml>
LAYOUT        circulation type; kitchen type + ventilation; entry sequence;
              flow (name the specific bad path); service area; orientation
              <each with mark>
FENG SHUI     财位 — always reported, with what physically occupies the corner
              <then only the other checks that fire, each with 中文 term>
              <state explicitly which were checked and did not fire>
SUITS         the household this layout serves well — be specific
LOOK ELSEWHERE the household it does not serve, stated as fit, never as fault
RESALE        buyer pool; what narrows it; single biggest mover
FIXABLE       renovable vs structural, with the remedy named where one exists
VERDICT       two sentences. Opens with what the plan does best, then the one
              trade-off that matters most. Never a judgement on the project.
UNAVAILABLE   what this plan cannot tell you, and what document would
```

**财位 is always reported**, even when unremarkable — it is the first thing a Mandarin-speaking
buyer looks for and the most legible thing on the drawing. Report the corner and what is in it.

## Worked example

Type B2, 646 sq ft / 60 sq m, two-bedroom, inclusive of 5 sq m balcony.
Unit plan plus the project legend/key-plan sheet.

```
UNIT
  Type B2, 646 sqft / 60 sqm, 2-bed 2-bath.
  Built into five blocks — A, B, C, D, E.                      [measured]

STRENGTHS
  AC ledge marked NON-STRATA — excluded from the 646 sqft, so
  no psf is paid on it. Most buyers never check this.          [measured]
  True dumbbell: no corridor anywhere in the plan.             [measured]
  Both bedrooms sit on external walls with their own glazing.  [measured]

DISCLAIMER
  "INCLUSIVE OF 5 SQM BALCONY"; AC ledge separately marked
  NON-STRATA on the drawing.                                   [measured]

AREA
  strata 646 sqft / 60 sqm                                     [measured]
  balcony 5 sqm = 8.3% of strata (5/60)                        [measured]
  internal ≈ 55 sqm / 592 sqft                                 [measured]
  void: none                                                   [measured]

ROOMS  (scale bar present on the legend sheet)
  Master: queen (1.52 x 1.90) with the wardrobe run opposite,
  ~0.7m walkway one side. Sleeping room, not a study.          [measured]
  Bedroom 2: super single sits comfortably. A queen fits only
  by crowding the wardrobe swing — worth seeing in person if
  it is meant as a second adult bedroom.                       [measured]
  Dining: four-seater. A six-seater would block the kitchen
  approach.                                                     [measured]

LAYOUT
  Dumbbell — living/dining connects the bedrooms, no corridor. [measured]
    Buys efficiency; costs acoustic privacy, since both
    bedrooms open onto the shared space. A genuine trade, and
    households differ on which side they want.
  Galley kitchen, open to dining, no door.                     [measured]
  Kitchen has no external window — sits inside the floor plate.[measured]
    Keeps the space feeling larger and suits light cooking.
    Daily wok cooking is the case to check in person: smell
    carries, and it cannot be closed off later.
  Flow: entry passes the kitchen run before reaching the
  living space.                                                 [measured]
  Orientation: DEPENDS ON STACK — B2 spans five blocks.        [measured]
    From the key plan (north up): Block B faces an
    expressway to the south; Block A faces the main road east;
    Block D faces a nature reserve north-west. Same type, three
    different products. Name the stack or say nothing.

FENG SHUI
  财位 — door at the lower right; the diagonal corner lands at
  the left edge of the living zone against the master bedroom
  wall. Solid two-wall corner, out of the traffic path — a
  good 财位 that takes a cabinet or plant.                      [inferred]
  穿堂煞 — the entry path turns; does not fire.                 [inferred]
  开门见灶 — stove near the entry sightline. Marginal; needs the
  actual door swing to call.                                    [inferred]
  门对门, 缺角 — checked, do not fire.                           [measured]
  路冲 — resolve per stack from the key plan.                   [measured]

SUITS
  A couple, a small family with one young child, or a landlord
  letting two rooms. Light cooks. Anyone who will actually use
  a 54 sqft balcony.

LOOK ELSEWHERE
  Households that host at a six-seater, cook with a wok daily,
  or need two full adult bedrooms.

RESALE
  Pool is wide — this is the most transacted unit shape in
  Singapore. Two things narrow it: the unventilated open
  kitchen, and the 8.3% balcony share on a small footprint.
  For stacks in block B, the expressway frontage narrows it further.

FIXABLE
  Bedroom 2 wardrobe clash — sliding doors solve it.
  Kitchen ventilation — structural, no external wall.
  Balcony share — structural.

VERDICT
  An efficient dumbbell with a genuinely non-strata AC ledge,
  which is worth more than most buyers realise. The trade is
  the kitchen: open, unventilated, and not changeable later.

UNAVAILABLE
  Floor level, actual view, and construction noise. Those need
  the stack chart and a site visit.
```

## Voice

Applies to everything this skill emits that a person will read or hear — captions, scripts,
on-screen text. Not to the schema, which is working notes.

**Run the deletion test on every sentence.** Delete it: does the reader lose a fact — a figure, a
name, a mechanism, a consequence? If nothing is lost, it was decoration. Cut it, or put a fact in
it. The full rubric lives in `scripts/deslop.py`; it is the same standard, do not invent a second
one.

The rewrite runs one direction: **shorter, plainer, flatter**. A sentence that states a fact and
stops is finished.

**A number gets the fact, not a characterisation of it.**

> ✗ "8.3% balcony — that's a lot of money for outdoor space."
> ✓ "Balcony is 5 of 60 sqm. You pay full psf on all of it."

**Singapore English, not American.** The register is plain, literal, unhurried.

| Write | Not |
|---|---|
| agent, salesperson | realtor |
| viewing | showing |
| psf, quantum | price point |
| en-bloc, MOP, COV, BTO, EC | (explain on first use for overseas viewers) |
| landed, terrace, semi-D | townhouse, single-family |

No imported desk idiom: *move the needle*, *low-hanging fruit*, *table stakes*, *double down*,
*banked*, *game-changer*, *no-brainer*. If a phrase would need explaining to a Singaporean
business owner, it is the wrong phrase.

**No hype and no manufactured urgency.** No countdowns, no "last unit", no invented scarcity — a
property-tenant rule, and it holds here.

**Mandarin output is Singapore Mandarin, not PRC or Taiwanese.** 组屋 not 公租房. 排屋 not
联排别墅. 新币 or 新元 for currency. Keep the English term where Singaporeans actually use it —
AC ledge, PES, MOP, BTO — and gloss it once. Writing mainland property vocabulary at a Singapore
audience reads as an outsider, which is the opposite of the positioning.

Singlish particles (lah, leh, hor) are a per-project decision, not a default. Ask before using
them; they warm a Reel and can undercut a figure in the same breath.

## Producing content from an analysis

The framing evidence is in `property/floorplans-social/output/` — do not re-derive it, and do not
invent hooks. The two findings that bind:

- **Never title anything 户型解析 / 户型详解.** Explainer framing ran at 0.10× the property-account
  median (n=23) and naming 户型 in a title at 0.14× (n=32). The word itself is a negative signal.
- **Question framing is the one shape both sweeps agree on** — 2.42× organic (n=22), +16pt in paid.

**Judge the fit, not the project.** That is what makes the question shape work without becoming an
attack. The hook asks the viewer to place themselves, rather than inviting them to sneer at
somebody's home.

| Use | Avoid | Why |
|---|---|---|
| `这个户型适合什么人？` | `这个户型你敢买吗` | Fit question, not a dare. Same shape, no target. |
| `买之前，我会先看这三个地方` | `这个户型的三大缺点` | First person plus a question the viewer has. |
| `同样面积，为什么这个感觉大一些？` | `这个户型很浪费` | Comparison without naming a loser. |
| `厨房没有窗，你介意吗？` | `厨房设计失败` | States the fact, hands over the judgement. |

First person also earned its place independently — +16pt in the paid sweep on n=94, and every
long-surviving Mandarin property account is built on it.

## Mandarin vocabulary

| English | 中文 | Trap |
|---|---|---|
| Strata / usable area | 实用面积 | Singapore has **no** 公摊面积. Say so — the PRC mental model imports it. |
| Efficiency | 得房率 | Means something different here, because there is no common-area deduction. |
| AC ledge | 空调架 | Check strata vs non-strata before praising or criticising it. |
| Bay window | 飘窗 | Common pre-2009, rare now. |
| Planter box | 花槽 | Dead area to most buyers; feng shui believers read it positively. |
| PES | 私人封闭空间 | |
| Household shelter | 防空壕 | Mandatory, counts in area, cannot be removed. |
| Dumbbell layout | 哑铃式户型 | |

## Guardrails

- **No figures from the plan that belong to `sgprop`.** Duties, ABSD, SSD, LTV, TDSR come from the
  CLI with provenance. A floorplan tells you area, never tax.
- **Feng shui is reported as market consequence, never as a spiritual claim.** "This narrows your
  buyer pool at exit" is defensible; anything about fortune is not.
- **Opinions are labelled as opinions**, and kept out of the `measured` rows.
- **This skill is a mechanism and carries no voice rules.** It works for the property tenant and
  for a property-agent client alike. Voice and compliance come from whichever tenant is calling
  it — the property spec, or that client's `CLIENT.md`. Do not bake either in here.

## Common mistakes

| Mistake | Fix |
|---|---|
| Eyeballing a vector PDF | Run `measure.py`. If the sheet has geometry, the numbers are exact and the findings become `measured`. |
| Trusting auto-detected scale without checking | A key plan's divider lines sit in the same bottom strip as the scale bar and can win the pitch. Verify with `--scale-only` against a 2.4 m carpark bay. |
| Skipping the area disclaimer | Read it first. It decides whether the ledge, balcony and void are inside the quoted area, and projects disagree. |
| Assuming the quoted area is living space | One strata terrace quoted 396 sqm; two carpark bays and the pool were 63.5 sqm of it, 16%. Measure the inclusions the disclaimer names. |
| Scoring a void as waste on an intermediate unit | With party walls both sides, the void at the core is the light well. Check `unit_position` first. |
| Calling the bigger unit bigger | Subtract the void. One resale type quoted 1,410 sqft but 183 of it was air above the living room; its 1,227 sqft sibling had more floor. |
| "Reasonably sized bedroom" | Name the bed and what is left. "Queen plus 0.7m one side, no desk" — never an adjective. |
| Praising an open kitchen without checking ventilation | Look for an external window. An internal open kitchen is permanent, and it is the top renovation regret. |
| Skipping 财位 because nothing is wrong with it | Always report it. It is the first thing a Mandarin-speaking buyer looks for. |
| Declaring orientation unavailable without looking | Check the sheet for a site plan and north arrow. Many developer plans print one. |
| Estimating an area the plan does not print | Mark `unknown`. Estimated areas get quoted back as fact. |
| Calling a dumbbell layout simply "good" | Record the acoustic-privacy trade-off. Buyers split on it. |
| Praising a non-strata AC ledge without checking the label | Read the drawing. Older plans include it. |
| Asserting orientation or view from a unit plan | `unavailable`. Needs the site plan. |
| Treating the household shelter as a design flaw | Mandatory in Singapore. Name it, don't score it. |
| Leading the content with 户型解析 | 0.10×. Ask a question instead. |
| Blurring measured and inferred | The one failure that destroys the format's credibility. |

---
Maintained by [bluebed property](https://property.bluebed.ai), a licensed agent's new-launch catalogue readable by your AI; built by [bluebed](https://bluebed.ai). Source: [github.com/danielkoh/sg-floorplan-skills](https://github.com/danielkoh/sg-floorplan-skills).
