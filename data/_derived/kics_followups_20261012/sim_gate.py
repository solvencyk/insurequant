"""sim_gate.py (parser-kics, ticket 20261012T1030Z) -- READ-ONLY on the repo.
Builds a candidate master = LIVE master + the named plans (in memory, guards applied), writes it to the scratch dir, runs
`scripts/validate_kics_disclosure.py --master <candidate>` in a subprocess (its own timeout), and compares the findings with a base run
keyed by (원보험사코드, 공시분기, rule).

usage:
  sim_gate.py --tag TAG [--plans a,b] [--base-report REPORT.json] [--scratch DIR] [--timeout 1200]
    --plans omitted/empty -> candidate = live master unchanged (use this to create the base run)
Prints: status counts, blocking-RED line, exit code, then the key-level diff vs the base report, grouped per (company, quarter).
Writes SCRATCH/gate_<TAG>.txt (stdout), SCRATCH/report_<TAG>.json (copy of the timestamped report the run printed), SCRATCH/cand_<TAG>.json.
"""
import copy
import json
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_followups_20261012")
from lib import *  # noqa: F401,F403,E402

utf8_stdout()
DEFAULT_SCRATCH = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/e15a5832-0270-4430-8e3e-4cba8a1f182c/scratchpad"


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def run_gate(master_path: Path, scratch: Path, tag: str, timeout: int):
    t0 = time.time()
    proc = subprocess.Popen([PY, "scripts/validate_kics_disclosure.py", "--master", str(master_path)], cwd=str(REPO),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise SystemExit(f"gate run for {tag} exceeded {timeout}s and was killed")
    text = out.decode("utf-8", errors="replace")
    (scratch / f"gate_{tag}.txt").write_text(text + f"\n--- stderr ---\n{err.decode('utf-8', errors='replace')[-2000:]}\nexit {proc.returncode}\n", encoding="utf-8", newline="\n")
    first = text.splitlines()[0] if text else ""
    rp = first.split("report:", 1)[1].strip() if "report:" in first else None
    assert rp and Path(rp).exists(), f"could not find report path in first stdout line: {first!r}"
    shutil.copyfile(rp, scratch / f"report_{tag}.json")
    return text, proc.returncode, scratch / f"report_{tag}.json", round(time.time() - t0, 1)


def fkey(f):
    return (f["원보험사코드"], f["공시분기"], f["rule"])


def main():
    tag = arg("--tag")
    plans = [x for x in (arg("--plans", "") or "").split(",") if x]
    scratch = Path(arg("--scratch", DEFAULT_SCRATCH))
    scratch.mkdir(parents=True, exist_ok=True)
    timeout = int(arg("--timeout", "1200"))
    rows = read_rows()
    live_sha = sha_file(MASTER)
    cand = copy.deepcopy(rows)
    touched = set()
    if plans:
        mp = merge_plans(plans)
        ne, ni = apply_to_rows(cand, mp)
        touched = {(e["code"], e["q"]) for e in mp["edits"]} | {(i["row"]["원보험사코드"], i["row"]["공시분기"]) for i in mp["inserts"]}
        print(f"candidate: plans={plans} edits={ne} inserts={ni} touched buckets={sorted(touched)}")
    cpath = scratch / f"cand_{tag}.json"
    cpath.write_bytes(dump_master_bytes(cand))
    print("candidate master:", cpath, "| live master sha", live_sha[:12], "| candidate sha", sha_file(cpath)[:12])
    text, rc, rep_path, secs = run_gate(cpath, scratch, tag, timeout)
    print("gate seconds:", secs, "| exit code:", rc)
    for ln in text.splitlines():
        if ln.startswith("Status counts") or "blocking RED" in ln:
            print("  ", ln.strip()[:260])
    rep = read_json(rep_path)
    base_path = arg("--base-report")
    if not base_path:
        return
    base = read_json(base_path)
    bf = {fkey(f): f for f in base["findings"]}
    cf = {fkey(f): f for f in rep["findings"]}
    assert len(bf) == len(base["findings"]) and len(cf) == len(rep["findings"]), "duplicate finding keys"
    added = sorted(set(cf) - set(bf))
    removed = sorted(set(bf) - set(cf))
    changed = [(k, bf[k], cf[k]) for k in sorted(set(bf) & set(cf)) if (bf[k]["status"], bf[k].get("expected"), bf[k].get("actual"), bf[k].get("diff")) != (cf[k]["status"], cf[k].get("expected"), cf[k].get("actual"), cf[k].get("diff"))]
    print(f"\nfinding keys: base {len(bf)} -> candidate {len(cf)} | added {len(added)} | removed {len(removed)} | changed (status or value) {len(changed)}")
    sc_b, sc_c = Counter(f["status"] for f in base["findings"]), Counter(f["status"] for f in rep["findings"])
    print("status counts base :", dict(sc_b))
    print("status counts cand :", dict(sc_c))
    outside = [k for k in added + removed + [c[0] for c in changed] if (k[0], k[1]) not in touched]
    print("keys outside the touched buckets that moved:", len(outside), outside[:10])
    per = defaultdict(list)
    for k in added:
        per[(k[0], k[1])].append(f"  + {k[2]}: {cf[k]['status']}  {str(cf[k].get('detail'))[:150]}")
    for k in removed:
        per[(k[0], k[1])].append(f"  - {k[2]}: was {bf[k]['status']}")
    for k, b, c in changed:
        per[(k[0], k[1])].append(f"  ~ {k[2]}: {b['status']} -> {c['status']} (exp {b.get('expected')}->{c.get('expected')}, act {b.get('actual')}->{c.get('actual')}, diff {b.get('diff')}->{c.get('diff')}) {str(c.get('detail'))[:160]}")
    for bucket in sorted(per):
        print(f"\n[{bucket[0]} {bucket[1]}]")
        for ln in per[bucket]:
            print(ln)
    # any RED anywhere that is new?
    new_red = [k for k in added if cf[k]["status"] == "RED"] + [c[0] for c in changed if c[2]["status"] == "RED" and c[1]["status"] != "RED"]
    gone_red = [k for k in removed if bf[k]["status"] == "RED"] + [c[0] for c in changed if c[1]["status"] == "RED" and c[2]["status"] != "RED"]
    print(f"\nNEW RED: {len(new_red)} {new_red}")
    print(f"RESOLVED RED: {len(gone_red)} {gone_red}")
    new_y = [k for k in added if cf[k]["status"] == "YELLOW"] + [c[0] for c in changed if c[2]["status"] == "YELLOW" and c[1]["status"] != "YELLOW"]
    gone_y = [k for k in removed if bf[k]["status"] == "YELLOW"] + [c[0] for c in changed if c[1]["status"] == "YELLOW" and c[2]["status"] != "YELLOW"]
    print(f"NEW YELLOW: {len(new_y)} {new_y}")
    print(f"RESOLVED YELLOW: {len(gone_y)} {gone_y}")


if __name__ == "__main__":
    main()
