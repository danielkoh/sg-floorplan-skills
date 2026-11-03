---
name: sg-space-planning
description: Use when furnishing or space-planning a Singapore condo, EC or landed unit from its floor plan — seeing which households a layout suits, deciding what a room can hold, making an awkward room work, laying a room out for a particular household (WFH couple, young family, grandparents staying, a first home for one), or preparing furniture layouts and coordinates for a Blender scene or a floor-plan video.
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

## Layout scan — run it first

`python3 <this skill>/traits.py <slug> [--type "<type>"]` (or `--all`); point it at your
checklists with `--data-dir <dir>` or `SG_FLOORPLAN_DATA`. It reads each unit type's layout
traits from `traits.yaml` — internal or open kitchens, entry without a foyer, corridor-set
bedrooms, fan-ventilated bathrooms, storage planned into the rooms, study nooks, compact
bedrooms, two-bedroom plans — and quotes the checklist text behind each. `--type` adds what each
trait gives a household day to day, who it suits, who should plan ahead for it, and how to make
it work. The summary gives each trait's share of every type scanned: **a trait most units share
is how new launches are built, so present it as "how to make it work", not as a difference
between units.**

Every trait is a lead. Confirm it on the plan image before it reaches a script; a space trait
(compact room, nook, entry without a foyer) then gets a layout through `fit.py`.

## Workflow

1. **Room model.** For each room you will furnish: clear width and depth, door position and
   swing arc, window wall, wardrobe extent, columns or DB cupboards. Tag each `measured` or
   `inferred`. For any wall you might suggest removing, read its type:
   `python3 <this skill>/walltype.py plan.png x1 y1 x2 y2` (a short segment
   across the wall). Solid shaded fill = structural, never removable; outline = partition, which
   opens the "take down a partition" idea via `sg-reno-rules`.
2. **Read the layout's traits.** Start from the layout scan, then add what only the drawing
   shows. Measured facts only: rooms under ~2.5 m clear, nooks and strips, long passages,
   fan-ventilated spaces, storage to plan, appliances sharing worktop. Say what each means for a
   household, in metres.
3. **Pick the household.** Use `suits` in `traits.yaml`: a household the layout suits, or one
   that `make_it_work` serves. One per layout. The question is "what does this room let *this*
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
2. **Traits**: each trait with its measurement and what it means day to day.
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
  `sg-reno-rules` first: `python3 <sg-reno-rules>/verify.py --idea "<idea>"`.
  Say it only if that prints a `SAY:` line for the unit's housing type, and say it with its
  conditions. Otherwise list it under Open items.
- **Nothing from `standards.yaml → unavailable`** (bunk headroom, wall-bed specs, sofa/TV
  distances) unless a named product's spec sheet is cited.
- **Positive, household-first wording, everywhere.** Copy says what the room holds and how one
  household makes it work. It never opens on what the unit lacks, never uses "problem", "issue",
  "inefficient", "wasted", "bad" or "buyers would mind", and never questions the developer's plan.
- **`make_it_work` items tagged `needs_reno_check` are never said** until a renovation rule
  confirms them.
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

---
Maintained by [bluebed property](https://property.bluebed.ai), a licensed agent's new-launch catalogue readable by your AI; built by [bluebed](https://bluebed.ai). Source: [github.com/danielkoh/sg-floorplan-skills](https://github.com/danielkoh/sg-floorplan-skills).
