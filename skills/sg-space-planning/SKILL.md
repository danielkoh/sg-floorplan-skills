---
name: sg-space-planning
description: Use when furnishing or space-planning a Singapore condo, HDB or landed unit from its floor plan — finding space inefficiencies, deciding what a room can hold, laying a room out for a particular household (WFH couple, young family, grandparents staying, a first home for one), or preparing furniture layouts and coordinates for a Blender scene or a floor-plan video.
---

# Singapore space planning

**A furniture layout is a claim about a real room. Check it with `fit.py` before anyone sees it.**
State the narrowest conclusion the evidence supports: "this footprint fits here with these
clearances", never "this room is great for a family". (Evidence rule adapted from
pascalorg/editor `furniture-fit`, MIT.)

`sg-floorplan-analysis` reads and judges the plan; this skill furnishes it. Sizes and
clearances live in `standards.yaml`, each with a source and grade. Read it first, every time.

## Inputs — get all three before laying anything out

1. **The plan image** for the unit type (the developer's brochure page, or your own export of it). Room data alone is not enough: doors, swings, windows and where the
   wardrobe actually sits come only from the drawing.
2. **The checklist row** for measured room sizes, if you keep one (`sg-floorplan-analysis` and
   `measure.py` produce them; schema in `CHECKLIST.md`). Without one, measure the rooms first. If it says "incl. wardrobe", find the wardrobe on the drawing and model its real
   extent; it often covers part of one wall, not the whole wall.
3. **The household**: who lives there and what they need the room to do.

Scale comes from a measured room in the checklist (pixels per metre off one wall), never by eye
alone. If neither the checklist nor a scale bar gives a dimension, mark it `inferred`.
**When the checklist and the image disagree, lay out on the smaller figure and say so.**
**Wardrobe doors are hinged (0.90 m in front) unless the drawing shows sliding doors.**

## Issue scan — run it first

`python3 <this skill>/issues.py <slug> [--type "<type>"]` (or `--all`); point it at your checklists with `--data-dir <dir>` or `SG_FLOORPLAN_DATA`
flags the layout issues that put buyers off, from `issues.yaml`: windowless or open kitchens,
no foyer, heavy circulation, windowless bathrooms, no shelter or yard, open study niches,
borrowed-light masters, shared bathrooms, narrow bedrooms, two bedrooms only. Each flag quotes
the checklist text behind it. `--type` adds what each issue costs a household, who it matters
less and more to, and the workarounds. The summary gives each issue's share of every type
scanned: **an issue on most units is not a reason to choose this one over another; frame it as
"how to live with it", not as a difference.**

Every flag is a lead. Confirm it on the plan image before it reaches a script; a space issue
(narrow room, niche, no foyer) then gets a layout through `fit.py`.

## Workflow

1. **Room model.** For each room you will furnish: clear width and depth, door position and
   swing arc, window wall, wardrobe extent, columns or DB cupboards. Tag each `measured` or
   `inferred`. For any wall you might suggest removing, read its type:
   `python3 <this skill>/walltype.py plan.png x1 y1 x2 y2` (a short segment
   across the wall). Solid shaded fill = structural, never removable; outline = partition, which
   opens the "take down a partition" workaround via `sg-reno-rules`.
2. **Find the inefficiencies (internal).** Start from the issue scan, then add what only the
   drawing shows. Measured facts only: rooms under ~2.5 m clear, niches
   and leftover strips, long passages, windowless spaces, missing shelter/yard storage,
   appliances eating worktop. Say what each costs a household, in metres.
3. **Pick the household.** Use `who_less` in `issues.yaml`: the household the unit's issues
   matter least to, or the one a workaround serves. One per layout. The question is "what does this room let *this*
   household do", not "who should buy this unit".
4. **Write the layout JSON** (format below) and run:
   `python3 <this skill>/fit.py layout.json`
   Every item that opens, folds or pulls out (wall bed, trundle, hinged wardrobe, sofa bed,
   extendable table) gets a `states` entry. **Only a PASS goes into the output.** On FAIL,
   change the furniture, not the clearance.
5. **Write the output contract.**

## Layout JSON

Metres; origin at a room corner; x across, y into the room; rectangles only.
`room {w,d}` clear floor · `door_entry {x,y,w,d}` floor just inside the door ·
`fixed[] {name, kind, x,y,w,d}` with kind `door_swing`, `wardrobe`, `column` ·
`items[] {name, x,y,w,d, use:{side:+x|-x|+y|-y, depth}, states:[{name,x,y,w,d}], may_cover:[]}` ·
`routes[] {name, x,y,w,d}` walkways that must stay open (past a niche, door to en suite); a
route that fails means the furniture moves — never delete the route to get a PASS.
`fit.py` flags `SHARED` when two use zones overlap: both still pass, but the output must say
those two items cannot be used at the same time (e.g. desk chair and bedside walkway).
`use.depth` comes from `standards.yaml` (bed side 0.60, desk chair 0.90, hinged wardrobe 0.90…).
Examples: `examples/example-3br-bed3-study-for-two.json` (PASS, read off a real plan), `examples/example-3br-bed2-queen-FAIL.json` (a finding kept as evidence), `examples/example-2br-bed2-wallbed-FAIL.json` (the open wall bed hitting the desk).

## Output contract

1. **Room model table**: dimension, value, mark.
2. **Findings**: each inefficiency with its measurement (internal wording allowed).
3. **Layout**: household, the layout JSON path, and the `fit.py` PASS report pasted in full,
   with every `SHARED` line restated in plain words. Keep any failed layout file as evidence of
   a finding ("a queen does not fit with hinged doors"), named `*-FAIL.json`, never for the scene.
   The JSON coordinates are the Blender scene; the artist builds from them, not from prose.
4. **Claims for the script**: one line per sayable fact, each with its mark and the
   `standards.yaml` key behind any clearance ("leaves 0.62 m beside the bed — bed_side_walkway").
5. **Open items**: anything `inferred` or `unavailable` that a script must not say.

## Hard limits

- **Loose furniture by default.** Anything drilled, hung or fixed (walls, ceilings, balconies,
  the household shelter), or any change to plumbing, appliances or walls, goes through
  `sg-reno-rules` first: `python3 <sg-reno-rules>/verify.py --workaround "<idea>"`.
  Say it only if that prints a `SAY:` line for the unit's housing type, and say it with its
  conditions. Otherwise list it under Open items.
- **Nothing from `standards.yaml → unavailable`** (bunk headroom, wall-bed specs, sofa/TV
  distances) unless a named product's spec sheet is cited.
- **Public wording leads with the household, not the unit.** Copy says what the room holds and
  how one household uses it. It never opens on what the unit lacks, never says "inefficient",
  "wasted" or "bad", and never questions the developer's plan. "Inefficiency" is a working word.
- **Workarounds tagged `needs_reno_check` are never said** until a renovation rule confirms them.
- **No verdicts on households.** "One way it works for a family of four", never "perfect for families".
- Hooks are not this skill's job. Research what is actually running in the category before writing one.

## Common mistakes (seen in baseline runs)

| Mistake | Fix |
|---|---|
| Wall bed or trundle drawn closed only; open, it hits the desk | `states` entry for every moving item; fit.py checks each |
| Wardrobe assumed to span the whole wall, and the door put on the same wall | Read both off the drawing; model the swing as `fixed` |
| "0.54 m each side" called comfortable | Compare with `standards.yaml`; 0.45–0.60 is "a tight squeeze" |
| Door and window positions guessed | They are on the plan image; load it |
| Ceiling drying rack, fridge column, wall shelves proposed | Check `sg-reno-rules`; say only a `SAY:` line, with its conditions |
| Script opens "No yard, no store room…" | Open on the household's situation |
| A walkway failed the check, so it was removed | Declare it in `routes`; move furniture until it passes |
| Desk chair and bed walkway share floor, unmentioned | Restate each `SHARED` line in the output |
