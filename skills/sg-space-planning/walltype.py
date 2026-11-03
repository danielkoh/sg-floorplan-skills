#!/usr/bin/env python3
"""Read whether a wall on a developer floor plan is solid-filled (structural) or outlined.

Usage:
    python3 walltype.py plan.png x1 y1 x2 y2      # pixel coords of a short segment drawn ACROSS the wall

Convention on Singapore developer plans (operator, 3 Nov 2026): walls drawn with a solid shaded
fill are structural (reinforced concrete) and cannot be hacked; walls drawn as an outline (two
lines with background between) are non-structural partitions. Check the sheet's legend when it
has one. A household-shelter wall is shaded and is never removable.

The segment should start in one room, cross the wall at right angles and end in the next room,
about 10-20 px either side of the wall. The tool samples the pixels along it and reports the
longest run of mid-grey fill (solid) versus line-background-line (outline).
"""
from __future__ import annotations

import sys

from PIL import Image


def profile(img, x1, y1, x2, y2):
    n = max(abs(x2 - x1), abs(y2 - y1)) + 1
    pts = [(round(x1 + (x2 - x1) * i / (n - 1)), round(y1 + (y2 - y1) * i / (n - 1))) for i in range(n)]
    return [sum(img.getpixel(p)[:3]) / 3 for p in pts]


def classify(vals):
    bg = max(vals)                       # the room's background is the lightest pixel
    # mid-grey fill: clearly darker than background, clearly lighter than ink lines
    fill = [bg - 25 > v > 60 for v in vals]
    ink = [v <= 60 for v in vals]
    run = best = 0
    for f in fill:
        run = run + 1 if f else 0
        best = max(best, run)
    ink_runs, prev = 0, False
    for k in ink:
        if k and not prev:
            ink_runs += 1
        prev = k
    if best >= 5:
        return "solid", best, ink_runs
    if ink_runs >= 2:
        return "outline", best, ink_runs
    return "unclear", best, ink_runs


def main(argv):
    if len(argv) != 6:
        print(__doc__)
        return 2
    img = Image.open(argv[1]).convert("RGB")
    x1, y1, x2, y2 = map(int, argv[2:])
    vals = profile(img, x1, y1, x2, y2)
    kind, fill_px, lines = classify(vals)
    verdict = {
        "solid": "SOLID fill: structural, not hackable",
        "outline": "OUTLINE: non-structural partition; removing it is a renovation (check sg-reno-rules)",
        "unclear": "UNCLEAR: re-draw the segment across the wall, or read it by eye and mark inferred",
    }[kind]
    print(f"{verdict}  (longest grey run {fill_px} px, ink lines crossed {lines})")
    print("profile:", " ".join(f"{int(v)}" for v in vals))
    return 0 if kind != "unclear" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
