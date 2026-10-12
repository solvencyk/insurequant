"""f3_datacontract_candidate.py CANDIDATE_MASTER -- the K-ICS-relevant data-contract checks (CHECK 1 census, 3 cross-source, 4 domain identity,
7 restatement ledger) run IN PROCESS on live records vs candidate records (validate_data_contract.py has no --master option).
Prints new / gone findings and RED counts.  READ-ONLY (Env() loads the live masters read-only; nothing is written)."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/src")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
import validate_data_contract as vdc  # noqa: E402

cand = read_rows(Path(sys.argv[1]))
if "--release" in sys.argv:        # in-memory only: judge the candidate as it will be after the two registry entries are removed from the code
    import validate_kics_disclosure as vkd  # noqa: E402
    for k in (("KR0003", "2025.1Q"), ("KR0032", "2024.3Q")):
        vkd._TIER2_ISSUER_INCONSISTENT.pop(k)
t0 = time.time()
env = vdc.Env()
live = list(env.kics_records)
CHECKS = (vdc.check_census, vdc.check_cross_source, vdc.check_domain_identity, vdc.check_kics_restatement)


def run(records):
    env.kics_records = records
    res = vdc.GateResult()
    for fn in CHECKS:
        fn(res, env)
    return {json.dumps([f.check, f.severity, f.rule, f.company, f.quarter, (f.message or "")[:200]], ensure_ascii=False) for f in res.findings}


base = run(live)
cur = run(cand)
new = sorted(cur - base)
gone = sorted(base - cur)
nred = lambda s: sum(1 for x in s if json.loads(x)[1] == "RED")
print(f"live: {len(base)} findings (RED {nred(base)}) | candidate: {len(cur)} findings (RED {nred(cur)}) | new {len(new)} (RED {nred(new)}) | gone {len(gone)} ({time.time()-t0:.0f}s)")
for x in new:
    print("  NEW :", x[:300])
for x in gone:
    print("  GONE:", x[:300])
