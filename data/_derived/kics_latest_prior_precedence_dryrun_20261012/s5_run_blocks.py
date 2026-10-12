"""s5_run_blocks.py -- step 5 (READ-ONLY on the repo): run the REAL K-ICS gate on temporary candidate masters, one block at a time.

  --baseline                  run the gate on the live master -> baseline_slim.json
  --ids KR0032_2024.3Q,...    evaluate those plans (plans/<id>.json)
  --all                       evaluate every plan in plans/ that has no result yet (resumable)
  --force                     re-evaluate even when a result exists

Each result line in block_eval.jsonl:  per-block gate comparison (bucket findings, neighbour findings, anything-else findings,
new extra-axis REDs, registry-machinery signals, status counts).  The verdict logic lives in s6_verdicts.py (so it can be iterated
without re-running the gates).
The candidate master is written to _tmp/ and deleted right after its run.  report_latest.json is restored at the end.
"""
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402
from harness import *  # noqa: F401,F403,E402

utf8_stdout()


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


PLANS = OUT / "plans"
RESULTS = OUT / "block_eval.jsonl"
BASE = OUT / "baseline_slim.json"


def baseline():
    TMP.mkdir(parents=True, exist_ok=True)
    slim, keep, rc, secs = run_gate(MASTER, "baseline")
    slim["_gate_lines"] = keep
    slim["_rc"] = rc
    slim["_master_sha"] = sha_file(MASTER)
    write_json_lf(BASE, slim, indent=None)
    print("baseline:", keep, "rc", rc, f"{secs}s", "master sha", slim["_master_sha"][:12])
    return slim


def done_ids():
    if not RESULTS.exists():
        return set()
    return {json.loads(ln)["id"] for ln in RESULTS.read_text(encoding="utf-8").splitlines() if ln.strip()}


def evaluate(plan_id, rows, base):
    plan = read_json(PLANS / f"{plan_id}.json")
    code, q = plan["code"], plan["quarter"]
    cand, n, derived = apply_plan(rows, plan)
    cpath = TMP / f"cand_{plan_id}.json"
    cpath.write_bytes(dump_master_bytes(cand))
    try:
        slim, keep, rc, secs = run_gate(cpath, plan_id)
    finally:
        try:
            cpath.unlink()
        except OSError:
            pass
    qs = [q] + [x for x in (qadd(q, d) for d in (-2, -1, 1, 2)) if x]
    own = {(code, q)}
    near = {(code, x) for x in qs[1:]}
    ch_all = finding_changes(base, slim)
    ch_bucket = [c for c in ch_all if tuple(c[0].split("|", 2)[:2]) in own]
    ch_near = [c for c in ch_all if tuple(c[0].split("|", 2)[:2]) in near]
    ch_other = [c for c in ch_all if tuple(c[0].split("|", 2)[:2]) not in own | near]
    new_x, gone_x = diff_extra(base, slim, "extra_red")
    new_r, gone_r = diff_extra(base, slim, "registry_red")
    res = {
        "id": plan_id, "code": code, "quarter": q, "n_cell_edits": n, "n_derived": len(derived), "derived": derived,
        "edits": [{k: e[k] for k in ("item", "field", "old", "new")} for e in plan["edits"]],
        "latest_src": plan.get("latest_src"), "latest_label": plan.get("latest_label"),
        "base_bucket_red": {k: v for k, v in red_set(base, code, q).items()},
        "cand_bucket_red": {k: v for k, v in red_set(slim, code, q).items()},
        "bucket_changes": ch_bucket, "neighbour_changes": ch_near, "other_changes": ch_other,
        "new_extra_red": new_x, "gone_extra_red": gone_x, "new_registry_red": new_r, "gone_registry_red": gone_r,
        "base_status": base["summary"], "cand_status": slim["summary"], "gate_lines": keep, "rc": rc, "secs": secs,
    }
    return res


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    try:
        if "--baseline" in sys.argv:
            baseline()
            return
        if not BASE.exists():
            raise SystemExit("run --baseline first")
        base = read_json(BASE)
        if sha_file(MASTER) != base["_master_sha"]:
            print("WARNING: live master sha differs from the baseline's -- another session changed it; re-run --baseline", sha_file(MASTER)[:12], base["_master_sha"][:12])
        rows = read_rows()
        ids = [x for x in (arg("--ids", "") or "").split(",") if x]
        if "--all" in sys.argv:
            ids = sorted(p.stem for p in PLANS.glob("*.json"))
        have = set() if "--force" in sys.argv else done_ids()
        todo = [i for i in ids if i not in have]
        print(f"{len(todo)} plans to run ({len(ids) - len(todo)} already done)")
        for k, pid in enumerate(todo, 1):
            t0 = time.time()
            try:
                res = evaluate(pid, rows, base)
            except Exception as e:  # noqa: BLE001
                res = {"id": pid, "error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-600:]}
            with open(RESULTS, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(res, ensure_ascii=False, default=str) + "\n")
            br = res.get("base_bucket_red") or {}
            cr = res.get("cand_bucket_red") or {}
            print(f"[{k}/{len(todo)}] {pid}: edits={res.get('n_cell_edits')} derived={res.get('n_derived')} bucketRED {len(br)}->{len(cr)} "
                  f"bucketΔ={len(res.get('bucket_changes') or [])} nearΔ={len(res.get('neighbour_changes') or [])} otherΔ={len(res.get('other_changes') or [])} "
                  f"newExtra={len(res.get('new_extra_red') or {})} newRegistry={len(res.get('new_registry_red') or {})} {time.time()-t0:.0f}s "
                  f"{res.get('error', '')}", flush=True)
    finally:
        pass   # report_latest.json is refreshed by one real live-master gate run at the very end of the job


if __name__ == "__main__":
    main()
