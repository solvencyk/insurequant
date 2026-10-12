"""s5b_datacontract_eval.py -- step 5b (READ-ONLY).  The K-ICS-relevant rules of the DATA-CONTRACT gate on the same candidate masters.

scripts/validate_data_contract.py has no --master option, so this runs it IN PROCESS: Env() loads the live masters read-only, then
`env.kics_records` is swapped for the candidate records (candidate = live master + one block overlay, in memory only) and the K-ICS-relevant
checks are run: CHECK 1 census, CHECK 3 cross-source (K-ICS vs other masters), CHECK 4 domain identity, CHECK 7 restatement ledger.
(CHECK 2 as-of, 6 gold overlay, 8 master xlsx are not K-ICS-value rules; the xlsx check would report DRIFT for any master change by design.)
Output: datacontract_eval.jsonl (one line per plan: findings that are NEW / GONE vs the baseline run on the live master).
"""
import json
import sys
import time

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402
from harness import apply_plan  # noqa: E402

utf8_stdout()
import validate_data_contract as vdc  # noqa: E402

t0 = time.time()
env = vdc.Env()
print(f"Env loaded in {time.time()-t0:.1f}s", flush=True)
rows = read_rows()
CHECKS = (vdc.check_census, vdc.check_cross_source, vdc.check_domain_identity, vdc.check_kics_restatement)


def run(records):
    env.kics_records = records
    res = vdc.GateResult()
    for fn in CHECKS:
        fn(res, env)
    return {json.dumps([f.check, f.severity, f.rule, f.company, f.quarter, (f.message or "")[:140]], ensure_ascii=False) for f in res.findings}


t1 = time.time()
base = run(rows)
print(f"baseline: {len(base)} findings, RED={sum(1 for x in base if json.loads(x)[1] == 'RED')} in {time.time()-t1:.1f}s", flush=True)
out = OUT / "datacontract_eval.jsonl"
done = set()
if out.exists():
    done = {json.loads(l)["id"] for l in out.read_text(encoding="utf-8").splitlines() if l.strip()}
ids = sorted(p.stem for p in (OUT / "plans").glob("*.json"))
n = 0
for pid in ids:
    if pid in done:
        continue
    plan = read_json(OUT / "plans" / f"{pid}.json")
    cand, ne, der = apply_plan(rows, plan)
    cur = run(cand)
    new = sorted(cur - base)
    gone = sorted(base - cur)
    rec = {"id": pid, "new": [json.loads(x) for x in new], "gone": [json.loads(x) for x in gone]}
    with open(out, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    n += 1
    print(f"{pid}: new={len(new)} (RED {sum(1 for x in rec['new'] if x[1]=='RED')}) gone={len(gone)}", flush=True)
env.kics_records = rows
print(f"done {n} plans in {time.time()-t0:.0f}s")
