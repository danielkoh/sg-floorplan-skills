"""Tests for the floor-plan skills' tools. Run: python3 -m pytest -q"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = os.path.join(ROOT, "skills", "sg-space-planning")
RR = os.path.join(ROOT, "skills", "sg-reno-rules")
FIX = os.path.join(ROOT, "tests", "fixtures")


def run(*args, env=None):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, env=env)


# ---- fit.py -------------------------------------------------------------

def test_fit_examples_match_their_names():
    for f in sorted(os.listdir(os.path.join(SP, "examples"))):
        r = run(os.path.join(SP, "fit.py"), os.path.join(SP, "examples", f))
        expect_fail = "FAIL" in f
        assert (r.returncode == 1) == expect_fail, f"{f}: {r.stdout}"


def test_fit_catches_open_state_overlap(tmp_path):
    layout = {"room": {"w": 3.2, "d": 2.6}, "door_entry": {"x": 2.6, "y": 0.9, "w": 0.6, "d": 0.8},
              "items": [{"name": "desk", "x": 0, "y": 0, "w": 2.4, "d": 0.6, "use": {"side": "+y", "depth": 0.9}},
                        {"name": "wall bed", "x": 0.4, "y": 2.15, "w": 1.65, "d": 0.45,
                         "states": [{"name": "open", "x": 0.4, "y": 0.5, "w": 1.65, "d": 2.1}]}]}
    p = tmp_path / "l.json"
    p.write_text(json.dumps(layout))
    r = run(os.path.join(SP, "fit.py"), str(p))
    assert r.returncode == 1 and "overlaps" in r.stdout


def test_fit_route_must_stay_clear(tmp_path):
    layout = {"room": {"w": 2.6, "d": 2.0}, "door_entry": {"x": 0, "y": 0.6, "w": 0.6, "d": 0.8},
              "routes": [{"name": "walkway", "x": 0.6, "y": 0.9, "w": 2.0, "d": 0.6}],
              "items": [{"name": "bookcase", "x": 1.5, "y": 1.0, "w": 0.8, "d": 0.4}]}
    p = tmp_path / "l.json"
    p.write_text(json.dumps(layout))
    r = run(os.path.join(SP, "fit.py"), str(p))
    assert r.returncode == 1 and "route 'walkway' blocked" in r.stdout


# ---- walltype.py ----------------------------------------------------------

def _plan(tmp_path):
    img = Image.new("RGB", (200, 100), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([40, 0, 55, 99], fill=(150, 150, 150), outline=(0, 0, 0))   # solid wall
    d.line([(140, 0), (140, 99)], fill=(0, 0, 0), width=2)                   # outline wall
    d.line([(150, 0), (150, 99)], fill=(0, 0, 0), width=2)
    p = tmp_path / "plan.png"
    img.save(p)
    return str(p)


def test_walltype_reads_solid_and_outline(tmp_path):
    p = _plan(tmp_path)
    solid = run(os.path.join(SP, "walltype.py"), p, "25", "50", "70", "50")
    outline = run(os.path.join(SP, "walltype.py"), p, "125", "50", "165", "50")
    assert solid.stdout.startswith("SOLID"), solid.stdout
    assert outline.stdout.startswith("OUTLINE"), outline.stdout


# ---- issues.py ------------------------------------------------------------

def _issues(*args):
    r = run(os.path.join(SP, "issues.py"), "example-residences", "--data-dir", FIX, "--json", *args)
    assert r.returncode == 0, r.stderr
    return {row["type"]: {f["id"] for f in row["flags"]} for row in json.loads(r.stdout)}


def test_issues_flags_from_checklist_text():
    got = _issues()
    assert {"kitchen_internal", "bathroom_no_window", "no_shelter_no_yard", "study_open_niche",
            "two_bedrooms_only"} <= got["2A"]
    assert "kitchen_window_to_ledge" in got["3B"] and "kitchen_internal" not in got["3B"]
    assert "no_shelter_no_yard" not in got["3B"]
    assert {"no_foyer", "shared_bathroom_two_bedrooms", "narrow_bedroom"} <= got["2C"]


def test_issues_bed_check_tries_both_orientations():
    # a 2.6 x 3.7 master takes a queen with the headboard on the long wall
    assert "tight_master_queen" not in _issues()["2A"]
    # a 2.3 x 3.0 master does not
    assert "tight_master_queen" in _issues()["2C"]


def test_issues_reads_env_data_dir():
    env = dict(os.environ, SG_FLOORPLAN_DATA=FIX)
    r = run(os.path.join(SP, "issues.py"), "example-residences", env=env)
    assert r.returncode == 0 and "Example Residences" in r.stdout


# ---- sg-reno-rules --------------------------------------------------------

def test_rules_pack_contract():
    import yaml
    pack = yaml.safe_load(open(os.path.join(RR, "rules.yaml")))
    ids = {r["id"] for r in pack["rules"]}
    for r in pack["rules"]:
        assert r["status"] in {"allowed", "conditional", "not_allowed", "check_mcst", "unverified"}, r["id"]
        assert r["source"]["url"] and r["source"]["fetched"], r["id"]
        if r["status"] != "unverified":
            assert r.get("quote") and r.get("say"), f"{r['id']}: a sayable rule needs a quote and a say line"
        if r["source"]["grade"] == "secondary":
            assert r["status"] in {"unverified", "check_mcst"}, f"{r['id']}: secondary source cannot assert"
    for k, refs in pack["workarounds"].items():
        assert set(refs) <= ids, k


def test_verify_runs_and_prints_say_lines():
    r = run(os.path.join(RR, "verify.py"), "--workaround", "glass in the balcony")
    assert "SAY:" in r.stdout and "balcony_no_enclosure" in r.stdout
