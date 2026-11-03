#!/usr/bin/env python3
"""Check a furnished room layout against geometry and clearances.

Usage:
    python3 fit.py layout.json            # human-readable report, exit 1 on any FAIL
    python3 fit.py layout.json --json     # machine-readable report

A layout is one room in metres, origin at a room corner, x across, y into the room.
Every item is an axis-aligned rectangle. Items may declare a `use` zone (the floor a
person needs in front of it to use it) and `states` (alternative footprints, e.g. a
wall bed open, a trundle pulled out, hinged wardrobe doors open). Each state is checked
as its own scene, together with every item in its default state.

Checks, per scene:
  1. inside    every footprint lies inside the room
  2. overlap   no two footprints overlap, and no footprint covers a fixed zone
               (door swing, wardrobe strip, column) unless the item names it in `may_cover`
  3. use       each item's use zone is free of other footprints
  4. reach     a person (disk of diameter `person_m`, default 0.6) can walk from the
               door to every use zone and every route without touching a footprint
  5. route     each declared `routes[]` zone (a walkway that must stay open, e.g. past a
               study niche) is free of every footprint and reachable from the door
  6. share     two use zones that overlap are reported (ok, but flagged): those two items
               cannot be used at the same time, and the output must say so

See SKILL.md for the layout format and standards.yaml for the sizes and clearances.
"""
from __future__ import annotations

import json
import sys
from collections import deque

EPS = 1e-6
GRID = 0.05  # metres per reachability cell


def rect(o):
    return (float(o["x"]), float(o["y"]), float(o["w"]), float(o["d"]))


def overlap(a, b):
    ax, ay, aw, ad = a
    bx, by, bw, bd = b
    ox = min(ax + aw, bx + bw) - max(ax, bx)
    oy = min(ay + ad, by + bd) - max(ay, by)
    return (ox, oy) if ox > EPS and oy > EPS else None


def use_zone(item, fp):
    """Rectangle of floor needed to use the item, on one side of its footprint."""
    u = item.get("use")
    if not u:
        return None
    x, y, w, d = fp
    depth = float(u["depth"])
    side = u["side"]
    if side == "+y":
        return (x, y + d, w, depth)
    if side == "-y":
        return (x, y - depth, w, depth)
    if side == "+x":
        return (x + w, y, depth, d)
    if side == "-x":
        return (x - depth, y, depth, d)
    raise ValueError(f"{item['name']}: use.side must be one of +x -x +y -y")


def scenes(layout):
    """Default scene plus one scene per declared state."""
    base = {it["name"]: rect(it) for it in layout["items"]}
    yield "default", base
    for it in layout["items"]:
        for st in it.get("states", []):
            s = dict(base)
            s[it["name"]] = rect(st)
            yield f"{it['name']}: {st['name']}", s


def reachable(room, fps, door, person):
    """Grid flood-fill of positions where a person's centre can stand."""
    W, D = room
    r = person / 2
    nx, ny = int(round(W / GRID)), int(round(D / GRID))

    def free(i, j):
        cx, cy = (i + 0.5) * GRID, (j + 0.5) * GRID
        if cx < r - EPS or cy < r - EPS or cx > W - r + EPS or cy > D - r + EPS:
            return False
        for fx, fy, fw, fd in fps:
            # distance from centre to rectangle
            dx = max(fx - cx, 0, cx - (fx + fw))
            dy = max(fy - cy, 0, cy - (fy + fd))
            if dx * dx + dy * dy < r * r - EPS:
                return False
        return True

    # door: start anywhere in the door's entry cell band
    sx, sy, sw, sd = door
    seen = set()
    q = deque()
    for i in range(nx):
        for j in range(ny):
            cx, cy = (i + 0.5) * GRID, (j + 0.5) * GRID
            if sx - EPS <= cx <= sx + sw + EPS and sy - EPS <= cy <= sy + sd + EPS and free(i, j):
                seen.add((i, j))
                q.append((i, j))
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (i + di, j + dj)
            if k not in seen and 0 <= k[0] < nx and 0 <= k[1] < ny and free(*k):
                seen.add(k)
                q.append(k)
    return seen


def touches(zone, seen):
    zx, zy, zw, zd = zone
    for i, j in seen:
        cx, cy = (i + 0.5) * GRID, (j + 0.5) * GRID
        if zx - EPS <= cx <= zx + zw + EPS and zy - EPS <= cy <= zy + zd + EPS:
            return True
    return False


def check(layout):
    W, D = float(layout["room"]["w"]), float(layout["room"]["d"])
    person = float(layout.get("person_m", 0.6))
    fixed = {f["name"]: (rect(f), f.get("kind", "fixed")) for f in layout.get("fixed", [])}
    door = rect(layout["door_entry"])
    items = {it["name"]: it for it in layout["items"]}
    results = []

    for scene, fps in scenes(layout):
        def add(check_name, ok, detail):
            results.append({"scene": scene, "check": check_name, "ok": ok, "detail": detail})

        # 1 inside
        for n, (x, y, w, d) in fps.items():
            ok = x >= -EPS and y >= -EPS and x + w <= W + EPS and y + d <= D + EPS
            add("inside", ok, f"{n} {'inside' if ok else f'outside the {W}x{D} room'}")

        # 2 overlap — items with items, items with fixed zones
        names = list(fps)
        for a in range(len(names)):
            for b in range(a + 1, len(names)):
                o = overlap(fps[names[a]], fps[names[b]])
                if o:
                    add("overlap", False, f"{names[a]} overlaps {names[b]} by {o[0]:.2f} x {o[1]:.2f} m")
        for n, fp in fps.items():
            allowed = set(items[n].get("may_cover", []))
            for fname, (frect, kind) in fixed.items():
                o = overlap(fp, frect)
                if o and fname not in allowed:
                    add("overlap", False, f"{n} covers {kind} '{fname}' by {o[0]:.2f} x {o[1]:.2f} m")

        # 3 use zones free
        solid = dict(fps)
        for fname, (frect, kind) in fixed.items():
            if kind != "door_swing":  # a door swing is floor you can stand in once the door is open
                solid[f"[{kind}] {fname}"] = frect
        for n, it in items.items():
            uz = use_zone(it, fps[n])
            if not uz:
                continue
            clear = True
            for m, fp in solid.items():
                if m == n:
                    continue
                o = overlap(uz, fp)
                if o:
                    clear = False
                    add("use", False, f"{n}: its {it['use']['depth']:.2f} m use zone is blocked by {m} ({o[0]:.2f} x {o[1]:.2f} m)")
            ux, uy, uw, ud = uz
            if ux < -EPS or uy < -EPS or ux + uw > W + EPS or uy + ud > D + EPS:
                clear = False
                add("use", False, f"{n}: use zone runs outside the room")
            if clear:
                add("use", True, f"{n}: {it['use']['depth']:.2f} m use zone clear")

        # 6 shared use zones
        uzs = [(n, use_zone(it, fps[n])) for n, it in items.items() if use_zone(it, fps[n])]
        for a in range(len(uzs)):
            for b in range(a + 1, len(uzs)):
                o = overlap(uzs[a][1], uzs[b][1])
                if o:
                    add("share", True, f"SHARED: {uzs[a][0]} and {uzs[b][0]} need the same {o[0]:.2f} x {o[1]:.2f} m of floor; not usable at once")

        # 5 routes must be free of footprints
        routes = layout.get("routes", [])
        for rt in routes:
            rr = rect(rt)
            blocked = False
            for m, fp in solid.items():
                o = overlap(rr, fp)
                if o:
                    blocked = True
                    add("route", False, f"route '{rt['name']}' blocked by {m} ({o[0]:.2f} x {o[1]:.2f} m)")
            if not blocked:
                add("route", True, f"route '{rt['name']}' clear ({rr[2]:.2f} x {rr[3]:.2f} m)")

        # 4 reach
        seen = reachable((W, D), list(solid.values()), door, person)
        if not seen:
            add("reach", False, f"no standing room for a {person:.2f} m person at the door")
            continue
        for rt in routes:
            ok = touches(rect(rt), seen)
            add("reach", ok, f"route '{rt['name']}': {'reachable' if ok else 'NOT reachable'} from the door")
        for n, it in items.items():
            uz = use_zone(it, fps[n])
            if not uz:
                continue
            ok = touches(uz, seen)
            add("reach", ok, f"{n}: {'reachable' if ok else 'NOT reachable'} from the door by a {person:.2f} m-wide person")

    return results


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    layout = json.load(open(argv[1]))
    res = check(layout)
    failed = [r for r in res if not r["ok"]]
    if "--json" in argv:
        print(json.dumps({"pass": not failed, "results": res}, indent=1))
    else:
        print(f"Layout: {layout.get('title', argv[1])}")
        print(f"Room {layout['room']['w']} x {layout['room']['d']} m (clear), person {layout.get('person_m', 0.6)} m")
        scene = None
        for r in res:
            if r["scene"] != scene:
                scene = r["scene"]
                print(f"\n  scene: {scene}")
            print(f"    {'ok  ' if r['ok'] else 'FAIL'} {r['check']:7} {r['detail']}")
        print(f"\n{'PASS' if not failed else f'FAIL ({len(failed)} problems)'}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
