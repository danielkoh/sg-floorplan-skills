#!/usr/bin/env python3
"""Freshness and sayability check for the renovation rules pack.

Usage:
    python3 verify.py                 # every rule: status, grade, age; exit 1 if a sayable rule is stale
    python3 verify.py <rule_id>       # one rule in full, ready to quote
    python3 verify.py --workaround "swap a gas hob for induction"   # the rules governing a workaround

A rule is sayable when its status is not `unverified`, it has a `say` line, and its source was
fetched within MAX_AGE_DAYS. Anything else must not reach a script or a client.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_AGE_DAYS = 90


def load():
    return yaml.safe_load(open(os.path.join(HERE, "rules.yaml")))


def age(rule, today):
    f = rule["source"].get("fetched")
    if isinstance(f, str):
        f = dt.date.fromisoformat(f)
    return (today - f).days if f else None


def sayable(rule, today):
    a = age(rule, today)
    return rule["status"] != "unverified" and bool(rule.get("say")) and a is not None and a <= MAX_AGE_DAYS


def show(rule, today):
    s = rule["source"]
    ok = sayable(rule, today)
    print(f"{rule['id']}  [{rule['status']}]  applies to {', '.join(rule['applies_to'])}")
    print(f"  {rule['topic']}")
    print(f"  rule: {' '.join(rule['rule'].split())}")
    if rule.get("quote"):
        print(f"  quote: \"{rule['quote']}\"")
    print(f"  source: {s['title']} — {s['url']}")
    print(f"          grade {s['grade']}, fetched {s.get('fetched')} ({age(rule, today)} days ago)"
          + (f", page updated {s['page_updated']}" if s.get("page_updated") else ""))
    if s.get("note"):
        print(f"  note: {s['note']}")
    if ok:
        print(f"  SAY: {rule['say']}")
        for d in rule.get("do_not_say", []):
            print(f"  never say: {d}")
    else:
        why = "status unverified" if rule["status"] == "unverified" else (
            "no say line" if not rule.get("say") else f"source older than {MAX_AGE_DAYS} days — re-fetch")
        print(f"  NOT SAYABLE: {why}")


def main(argv):
    pack = load()
    today = dt.date.today()
    rules = {r["id"]: r for r in pack["rules"]}
    if "--workaround" in argv:
        key = argv[argv.index("--workaround") + 1]
        ids = pack["workarounds"].get(key)
        if not ids:
            print(f"No rules mapped for '{key}'. Known workarounds:")
            for k in pack["workarounds"]:
                print(f"  - {k}")
            return 2
        for i in ids:
            show(rules[i], today)
            print()
        return 0
    if len(argv) > 1 and not argv[1].startswith("--"):
        show(rules[argv[1]], today)
        return 0
    stale = 0
    for r in pack["rules"]:
        a = age(r, today)
        flag = "ok" if sayable(r, today) else ("UNVERIFIED" if r["status"] == "unverified" else "STALE")
        if flag == "STALE":
            stale += 1
        print(f"{flag:10} {r['id']:32} {r['status']:12} {r['source']['grade']:9} {a:4d}d  {r['topic']}")
    print(f"\n{len(rules)} rules; {sum(sayable(r, today) for r in pack['rules'])} sayable; "
          f"{sum(r['status'] == 'unverified' for r in pack['rules'])} unverified; {stale} stale")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
