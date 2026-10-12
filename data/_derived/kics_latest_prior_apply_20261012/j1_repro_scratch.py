"""j1_repro_scratch.py -- would an explicit re-run of the fill_* chain overwrite the 65 ticket cells?  (SCRATCH COPY ONLY, live master untouched)

Same method as the 2026-10-11 reproducibility run (data/disclosure/_meta/kics_newer_editions_20261011/repro_20261011): the fill scripts are imported,
their module-level JSON_PATH is pointed at a scratch copy and main() runs with --period for the filing periods of the 16 blocks:
fill_period (--refresh) -> fill_subitems (--refresh) -> fill_market_subitems -> fill_post_transition.  Afterwards the scratch copy is compared with the live
master cell by cell: which of the 65 cells keep the new value, which go back to the old (as-filed) value, which become something else; plus how many OTHER
cells the chain moves (pre-existing noise, not part of this ticket).  The live master sha and `git status` are checked before and after.
usage: j1_repro_scratch.py [--compare-only]
"""
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
TMP = OUT / "_tmp" / "repro"
COPY = TMP / "master_copy.json"
PERIODS = ["FY2023_Q1", "FY2023_Q2", "FY2023_Q4", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4", "FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2026_Q1"]
STEPS = [("fill_period_to_disclosure.py", ["--refresh"]), ("fill_subitems_to_disclosure.py", ["--refresh"]),
         ("fill_market_subitems_to_disclosure.py", []), ("fill_post_transition_to_disclosure.py", [])]
RUNNER = '''import importlib.util, sys
from pathlib import Path
REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(REPO / "scripts"))
script, jcopy = sys.argv[1], sys.argv[2]
args = sys.argv[sys.argv.index("--") + 1:]
spec = importlib.util.spec_from_file_location("fillmod", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
assert Path(mod.JSON_PATH).resolve() == (REPO / "kics_disclosure.json").resolve()
mod.JSON_PATH = Path(jcopy)
raise SystemExit(mod.main(args))
'''


def git_status():
    return subprocess.run(["git", "status", "--short"], cwd=REPO, capture_output=True, text=True, encoding="utf-8").stdout


def run_chain():
    TMP.mkdir(parents=True, exist_ok=True)
    live_sha = sha_file(MASTER)
    gs0 = git_status()
    COPY.write_bytes(MASTER.read_bytes())
    (TMP / "runner.py").write_text(RUNNER, encoding="utf-8", newline="\n")
    for fn, extra in STEPS:
        args = extra + [a for p in PERIODS for a in ("--period", p)]
        cmd = [PY, str(TMP / "runner.py"), str(REPO / "scripts" / fn), str(COPY), "--"] + args
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(REPO), timeout=1500)
        (TMP / f"{fn}.log").write_text(r.stdout + "\n--STDERR--\n" + r.stderr, encoding="utf-8")
        import shutil
        shutil.copyfile(COPY, TMP / f"after_{fn}.json")
        print(f"{fn}: rc {r.returncode} {time.time()-t0:.0f}s stdout lines {len(r.stdout.splitlines())}", flush=True)
    assert sha_file(MASTER) == live_sha, "LIVE MASTER CHANGED during the scratch run"
    gs1 = git_status()
    print("live master sha unchanged:", sha_file(MASTER)[:12], "| git status identical before/after:", gs0 == gs1)
    if gs0 != gs1:
        print("   git status DIFF:\n", set(gs1.splitlines()) ^ set(gs0.splitlines()))


def compare():
    live = read_rows()
    mp = merge_plans(APPLIED)
    lm = {(*key(r),): r for r in live}
    out = {}
    for name in ["fill_period_to_disclosure.py"] + [s[0] for s in STEPS[1:]]:
        p = TMP / f"after_{name}.json"
        if not p.exists():
            continue
        cm = {key(r): r for r in read_rows(p)}
        kept = rev = other = missing = 0
        det = {"reverted": [], "other": []}
        for e in mp["edits"]:
            k = (e["code"], e["q"], e["item"])
            r = cm.get(k)
            if r is None:
                missing += 1
                continue
            v = r.get(e["field"], "<nokey>")
            if v == e["new"]:
                kept += 1
            elif v == e["old"]:
                rev += 1
                det["reverted"].append((k, e["field"], e["old"], e["new"]))
            else:
                other += 1
                det["other"].append((k, e["field"], v, e["old"], e["new"]))
        out[name] = (kept, rev, other, missing, det)
    # after the full chain
    last = TMP / "after_fill_post_transition_to_disclosure.py.json"
    cm = {key(r): r for r in read_rows(last)}
    kept = rev = other = missing = 0
    det = {"reverted": [], "other": []}
    for e in mp["edits"]:
        k = (e["code"], e["q"], e["item"])
        r = cm.get(k)
        if r is None:
            missing += 1
            continue
        v = r.get(e["field"], "<nokey>")
        if v == e["new"]:
            kept += 1
        elif v == e["old"]:
            rev += 1
            det["reverted"].append((k, e["field"], e["old"], e["new"]))
        else:
            other += 1
            det["other"].append((k, e["field"], v, e["old"], e["new"]))
    print("\nplanned cells after the FULL chain on the scratch copy: kept new value", kept, "| reverted to old", rev, "| other value", other, "| row missing", missing)
    by_kind = {}
    pk = {(e["code"], e["q"], e["item"], e["field"]): e["kind"] for e in mp["edits"]}
    for k, f, old, new in det["reverted"]:
        by_kind[pk[(*k, f)]] = by_kind.get(pk[(*k, f)], 0) + 1
    print("   reverted cells by kind:", by_kind)
    for x in det["reverted"]:
        print("   REVERTED:", x)
    for x in det["other"]:
        print("   OTHER   :", x)
    # per-step attribution
    for name, (kept, rev, other, missing, _d) in out.items():
        print(f"   after {name}: kept {kept} reverted {rev} other {other} missing {missing}")
    # noise: cells moved by the chain outside the 65 ticket cells
    planned_keys = {(e["code"], e["q"], e["item"], e["field"]) for e in mp["edits"]}
    moved = 0
    moved_in_touched = 0
    touched = {(e["code"], e["q"]) for e in mp["edits"]}
    for k, r in cm.items():
        lr = lm.get(k)
        if lr is None:
            moved += 1
            continue
        for f in ("값", "값_적용후"):
            if lr.get(f, "<nokey>") != r.get(f, "<nokey>") and (*k, f) not in planned_keys:
                moved += 1
                if (k[0], k[1]) in touched:
                    moved_in_touched += 1
    print(f"other cells the chain moves (not ticket cells; pre-existing behaviour): {moved} (inside the 16 touched buckets: {moved_in_touched})")
    print("rows added/removed by the chain:", len(cm) - len(lm), "net")


if "--compare-only" not in sys.argv:
    run_chain()
compare()
