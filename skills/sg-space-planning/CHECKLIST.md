# Floorplan checklist format

`issues.py` reads one JSON file per project: `<data-dir>/<project-slug>/floorplan-checklist.draft.json`.

```json
{
  "_meta": {"project": "Example Residences"},
  "rows": [
    {
      "type": "C1",
      "category": "3-Bedroom",
      "strata_sqft": 872,
      "unit_count": 15,
      "bed_bath": "3 bed / 2 bath",
      "room_dims": "master 2.9x3.85 (0.7 m wardrobe); bedroom2 2.45x3.25 (0.7 m wardrobe); bedroom3 2.3x3.25",
      "kitchen_window": "none (internal kitchen)",
      "kitchen_enclosure": "open kitchen beside the dining",
      "bathrooms_without_window": "Master Bath; Bath 2",
      "household_shelter": "none drawn",
      "yard": "none",
      "study": "study niche about 0.7 x 1.6 m, open, no window",
      "circulation_pct": 11.5,
      "family_name": "3-Bedroom, no foyer",
      "minuses": "No foyer: the front door opens into the kitchen | Kitchen has no window"
    }
  ]
}
```

Every field is optional; an issue whose fields are missing simply does not fire. Text fields are
read as written, so write what the drawing shows ("none", "internal kitchen", "no window") rather
than codes. `room_dims` is `name WxD` pairs separated by `;`, with `(0.7 m wardrobe)` after any room
whose size includes a wardrobe run. `minuses` may be a string with ` | ` separators or a list.
`sg-floorplan-analysis` produces these fields when it reads a plan.
