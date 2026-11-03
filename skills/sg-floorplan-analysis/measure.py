#!/usr/bin/env python3
"""Measure a vector floorplan PDF: derive scale from the scale bar, then size rooms.

Developer floorplans are usually vector, not scans. When they are, room dimensions
are exact rather than eyeballed — which moves findings from `inferred` to `measured`,
the distinction the whole rubric turns on.

    python3 measure.py plan.pdf                 # auto-detect scale, list rooms
    python3 measure.py plan.pdf --ppm 18.84     # force points-per-metre
    python3 measure.py plan.pdf --scale-only    # just show scale-bar candidates

A scan returns no geometry. That is the signal to fall back to scaling off a 0.9 m
door leaf and mark everything `inferred`.
"""
import argparse
import sys
from collections import defaultdict

try:
    import fitz  # pymupdf
except ImportError:
    sys.exit("needs pymupdf:  pip install pymupdf")


def collect_segments(page, y_limit):
    """Split vector items into vertical and horizontal wall lines."""
    vert, horiz = defaultdict(list), defaultdict(list)
    for group in page.get_drawings():
        if group["rect"].y1 > y_limit:
            continue
        for item in group["items"]:
            if item[0] == "l":
                a, b = item[1], item[2]
                if abs(a.x - b.x) < 0.6 and abs(a.y - b.y) > 4:
                    vert[round(a.x, 1)].append((min(a.y, b.y), max(a.y, b.y)))
                elif abs(a.y - b.y) < 0.6 and abs(a.x - b.x) > 4:
                    horiz[round(a.y, 1)].append((min(a.x, b.x), max(a.x, b.x)))
            elif item[0] == "re":
                r = item[1]
                if r.width < 1.5 and r.height > 4:
                    vert[round(r.x0, 1)].append((r.y0, r.y1))
                if r.height < 1.5 and r.width > 4:
                    horiz[round(r.y0, 1)].append((r.x0, r.x1))
    return vert, horiz


def find_scale(page):
    """Locate the scale bar by its evenly spaced ticks in the bottom strip.

    Returns (points_per_metre, note). The bar is a row of short vertical ticks at a
    constant pitch; that pitch is one scale unit, normally 1 m.

    Ticks are grouped by shared baseline before measuring pitch. Without that, a key
    plan's unit-divider lines sit in the same strip and win the modal gap — on the
    strata-terrace sheet they returned 11.3pt against a true 18.84pt.
    """
    h = page.rect.height
    rows = defaultdict(set)
    for group in page.get_drawings():
        r = group["rect"]
        if r.y0 < h * 0.80:  # bottom strip only
            continue
        if r.width < 1.5 and 3 < r.height < 16:
            rows[round(r.y0)].add(round(r.x0, 1))

    best = None
    for baseline, xset in rows.items():
        xs = sorted(xset)
        if len(xs) < 3:
            continue
        gaps = [round(b - a, 2) for a, b in zip(xs, xs[1:]) if 4 < b - a < 200]
        if len(gaps) < 2:
            continue
        buckets = defaultdict(list)
        for g in gaps:
            buckets[round(g)].append(g)
        run = max(buckets.values(), key=len)
        if len(run) < 2:
            continue
        pitch = sum(run) / len(run)
        # Prefer the longest regular run; break ties on the rightmost bar, since
        # the scale bar conventionally sits in the bottom-right corner.
        score = (len(run), max(xs))
        if best is None or score > best[0]:
            best = (score, pitch, len(run), baseline)

    if not best:
        return None, "no regular tick run found — treat as a scan"
    _, pitch, n, baseline = best
    return pitch, f"{n} equal intervals at {pitch:.2f}pt on baseline y={baseline}"


def cluster(values, tol=1.2):
    values = sorted(values)
    out, cur = [], [values[0]]
    for v in values[1:]:
        if v - cur[-1] <= tol:
            cur.append(v)
        else:
            out.append(sum(cur) / len(cur))
            cur = [v]
    out.append(sum(cur) / len(cur))
    return out


def bound_label(x, y, vert, horiz):
    """Nearest wall on each side of a room label."""
    left = max((v for v, sp in vert.items()
                if v < x - 2 and any(a <= y <= b for a, b in sp)), default=None)
    right = min((v for v, sp in vert.items()
                 if v > x + 2 and any(a <= y <= b for a, b in sp)), default=None)
    top = max((hh for hh, sp in horiz.items()
               if hh < y - 2 and any(a <= x <= b for a, b in sp)), default=None)
    bot = min((hh for hh, sp in horiz.items()
               if hh > y + 2 and any(a <= x <= b for a, b in sp)), default=None)
    return left, right, top, bot


BEDS = [("king 1.82", 1.82), ("queen 1.52", 1.52), ("super single 1.07", 1.07)]


def bed_fit(short_side_m):
    """Largest bed with at least a 0.6 m walkway beside it."""
    for name, w in BEDS:
        if short_side_m >= w + 0.6:
            return name
    return "single only"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--ppm", type=float, help="points per metre, overrides detection")
    ap.add_argument("--scale-only", action="store_true")
    ap.add_argument("--page", type=int, default=0)
    args = ap.parse_args()

    page = fitz.open(args.pdf)[args.page]
    detected, note = find_scale(page)
    ppm = args.ppm or detected

    print(f"scale-bar detection: {note}")
    if not ppm:
        sys.exit("no scale. Re-run with --ppm, or treat every dimension as `inferred`.")
    print(f"using 1 m = {ppm:.2f} pt\n")
    if args.scale_only:
        return

    # Plans usually sit above the title block; captions and legends below it.
    y_limit = page.rect.height * 0.72
    vert, horiz = collect_segments(page, y_limit)
    if not vert or not horiz:
        sys.exit("no wall geometry — this is a scan. Everything is `inferred`.")

    labels = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if text and span["bbox"][1] < y_limit and len(text) > 2:
                    labels.append((text, span["bbox"][0], span["bbox"][1]))

    print(f"{'label':24}{'width':>8}{'depth':>8}{'area':>10}   note")
    print("-" * 72)
    for text, x, y in labels:
        left, right, top, bot = bound_label(x, y, vert, horiz)
        if None in (left, right, top, bot):
            continue
        w, dp = (right - left) / ppm, (bot - top) / ppm
        if not (1.0 < w < 25 and 1.0 < dp < 30):
            continue
        note = ""
        upper = text.upper()
        if "BEDROOM" in upper or "MASTER" in upper:
            note = bed_fit(min(w, dp))
        elif "DINING" in upper:
            note = ("8-seater" if max(w, dp) >= 3.7 else
                    "6-seater" if max(w, dp) >= 3.3 else "4-seater")
        print(f"{text[:23]:24}{w:7.2f}m{dp:7.2f}m{w*dp:8.1f}sqm   {note}")

    print("\nWall-bounded rectangles only. A label inside an open-plan zone reports the")
    print("whole zone, not a room — check anything that looks too deep by hand.")


if __name__ == "__main__":
    main()
