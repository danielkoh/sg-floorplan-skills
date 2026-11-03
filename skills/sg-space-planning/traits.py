#!/usr/bin/env python3
"""Scan floorplan checklist rows for layout traits: what each layout suits, and how to make it work.

Usage:
    python3 traits.py <slug> [<slug> ...]          # per-type table, then how common each trait is
    python3 traits.py <slug> --type "2BR S1"       # one unit type, with who it suits and how to make it work
    python3 traits.py --all                        # every project with a checklist
    add --json for machine-readable output

Reads <data-dir>/<slug>/floorplan-checklist.draft.json and traits.yaml. The data dir is
--data-dir <dir>, else $SG_FLOORPLAN_DATA, else the current directory. Every flag carries
the checklist text that triggered it, so nothing is asserted that the checklist does not say.
A flag is a lead: confirm it on the plan image before it reaches a script.
"""
from __future__ import annotations

import glob
import json
import os
import re
import statistics
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS = None  # set in main()


def data_dir(argv):
    if "--data-dir" in argv:
        return argv[argv.index("--data-dir") + 1]
    if os.environ.get("SG_FLOORPLAN_DATA"):
        return os.environ["SG_FLOORPLAN_DATA"]
    return "."


def text(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return " | ".join(text(x) for x in v)
    if isinstance(v, dict):
        return " | ".join(f"{k}: {text(x)}" for k, x in v.items())
    return str(v)


def wardrobe_depths(row):
    """{room name: wardrobe depth} when room_dims says the size includes a wardrobe run."""
    out = {}
    for part in text(row.get("room_dims")).split(";"):
        m = re.search(r"([a-z_ ]+?)\s*[\d.]+\s*x\s*[\d.]+\s*\(([\d.]+)\s*m wardrobe", part.strip(), re.I)
        if m:
            out[m.group(1).strip().lower()] = float(m.group(2))
    return out


def bed_fits(a, b, bed_w, bed_l, side, foot):
    """Bed with walkways both sides and at the foot, either orientation."""
    return (a >= bed_w + 2 * side and b >= bed_l + foot) or (b >= bed_w + 2 * side and a >= bed_l + foot)


def room_sides(row):
    """Parse 'master 2.9x3.85 (...); bedroom2 2.45x3.25' into {name: (a, b)}."""
    out = {}
    for part in text(row.get("room_dims")).split(";"):
        m = re.search(r"([a-z_ ]+?)\s*([\d.]+)\s*x\s*([\d.]+)", part.strip(), re.I)
        if m:
            out[m.group(1).strip().lower()] = (float(m.group(2)), float(m.group(3)))
    return out


def match_rule(rule, row):
    """Return evidence text if the rule matches the row, else None."""
    if "any" in rule:
        for r in rule["any"]:
            ev = match_rule(r, row)
            if ev:
                return ev
        return None
    if "all" in rule:
        ev = [match_rule(r, row) for r in rule["all"]]
        return " ; ".join(ev) if all(ev) else None
    fields = rule.get("any_field") or [rule["field"]]
    rx = re.compile(rule["pattern"], re.I)
    ex = re.compile(rule["exclude"], re.I) if rule.get("exclude") else None
    for f in fields:
        for piece in text(row.get(f)).split(" | "):
            if rx.search(piece) and not (ex and ex.search(piece)):
                return f"{f}: {piece.strip()[:140]}"
    return None


def computed(rule, row, ctx):
    kind = rule["computed"]
    if kind == "circulation_top_quartile":
        pct = row.get("circulation_pct")
        q = ctx["circ_q3"].get(row.get("category"))
        if isinstance(pct, (int, float)) and q is not None and pct >= q:
            return f"circulation_pct: {pct}% (top quarter of measured {row.get('category')} types: >= {q:.1f}%, n={ctx['circ_n'][row.get('category')]})"
        return None
    sides = room_sides(row)
    t = rule.get("threshold_m")
    if kind == "bed_with_both_sides":
        wd = wardrobe_depths(row)
        for name, (a, b) in sides.items():
            if not name.startswith(rule["room"]):
                continue
            w = wd.get(name, 0.0)
            # wardrobe on an unknown wall: try taking it off either side
            cands = [(a - w, b), (a, b - w)] if w else [(a, b)]
            if not any(bed_fits(x, y, rule["bed_w"], rule["bed_l"], rule["side"], rule["foot"]) for x, y in cands):
                note = f", less a {w} m wardrobe" if w else ""
                return (f"room_dims: {name} {a}x{b}{note}: no orientation leaves {rule['side']} m both sides "
                        f"and {rule['foot']} m at the foot of a {rule['bed_w']} x {rule['bed_l']} m bed")
        return None
    if kind == "any_bedroom_min_side_at_most":
        hits = [f"{n} {a}x{b}" for n, (a, b) in sides.items()
                if not n.startswith("study") and min(a, b) <= t]
        return f"room_dims: {', '.join(hits)} (narrow side <= {t} m)" if hits else None
    raise ValueError(kind)


def load(slug):
    p = os.path.join(DRAFTS, slug, "floorplan-checklist.draft.json")
    d = json.load(open(p))
    return d.get("_meta", {}).get("project", slug), d["rows"]


def build_ctx(all_rows):
    by_cat = {}
    for r in all_rows:
        if isinstance(r.get("circulation_pct"), (int, float)):
            by_cat.setdefault(r.get("category"), []).append(r["circulation_pct"])
    q3, n = {}, {}
    for cat, vals in by_cat.items():
        if len(vals) >= 4:
            q3[cat] = statistics.quantiles(vals, n=4)[2]
            n[cat] = len(vals)
    return {"circ_q3": q3, "circ_n": n}


def scan(slugs):
    spec = yaml.safe_load(open(os.path.join(HERE, "traits.yaml")))
    projects = [(s, *load(s)) for s in slugs]
    # quartiles use every project with a checklist, so a small project is compared fairly
    every = []
    for p in glob.glob(os.path.join(DRAFTS, "*", "floorplan-checklist.draft.json")):
        every += json.load(open(p))["rows"]
    ctx = build_ctx(every)
    out = []
    for slug, project, rows in projects:
        for row in rows:
            flags = []
            for iss in spec["traits"]:
                rule = iss["detect"]
                ev = computed(rule, row, ctx) if "computed" in rule else match_rule(rule, row)
                if ev and any(f["id"] in iss.get("unless", []) for f in flags):
                    ev = None
                if ev:
                    flags.append({"id": iss["id"], "title": iss["title"], "evidence": ev})
            out.append({"slug": slug, "project": project, "type": row.get("type"),
                        "category": row.get("category"), "sqft": row.get("strata_sqft"),
                        "units": row.get("unit_count"), "flags": flags})
    return spec, out


def main(argv):
    global DRAFTS
    DRAFTS = data_dir(argv)
    dd = argv[argv.index("--data-dir") + 1] if "--data-dir" in argv else None
    as_json = "--json" in argv
    one = argv[argv.index("--type") + 1] if "--type" in argv else None
    if "--all" in argv:
        slugs = sorted(os.path.basename(os.path.dirname(p)) for p in
                       glob.glob(os.path.join(DRAFTS, "*", "floorplan-checklist.draft.json")))
    else:
        slugs = [a for a in argv[1:] if not a.startswith("--") and a not in (one, dd)]
    if not slugs:
        print(__doc__)
        return 2
    spec, res = scan(slugs)
    if one:
        res = [r for r in res if r["type"] == one]
    if as_json:
        print(json.dumps(res, indent=1, ensure_ascii=False))
        return 0
    traits = {i["id"]: i for i in spec["traits"]}
    for r in res:
        print(f"\n## {r['project']} {r['type']} — {r['category']}, {r['sqft']} sqft"
              + (f", {r['units']} units" if r["units"] else ""))
        if not r["flags"]:
            print("   no traits detected from the checklist")
        for f in r["flags"]:
            print(f"   - {f['title']}  [{f['evidence']}]")
            if one:
                iss = traits[f["id"]]
                print(f"       day to day: {iss['day_to_day']}")
                print(f"       suits: {'; '.join(iss['suits'])}")
                print(f"       plan ahead if: {'; '.join(iss['plan_ahead'])}")
                for w in iss["make_it_work"]:
                    if isinstance(w, dict):
                        print(f"       make it work (renovation: say only once sg-reno-rules confirms): {w['text']}")
                        if w.get("reno_idea"):
                            print(f"         -> python3 <sg-reno-rules>/verify.py --idea \"{w['reno_idea']}\"")
                    else:
                        print(f"       make it work: {w}")
    print("\n## How common each trait is — share of unit types scanned")
    for iss in spec["traits"]:
        hits = [r for r in res if any(f["id"] == iss["id"] for f in r["flags"])]
        if hits:
            print(f"   {len(hits):3d} of {len(res)} ({100*len(hits)/len(res):.0f}%)  {iss['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
