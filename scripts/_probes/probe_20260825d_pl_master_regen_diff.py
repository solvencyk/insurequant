# -*- coding: utf-8 -*-
"""build_pl_breakdown.py 재실행 전/후 pl_breakdown_master.json 을 combo-diff 하고, 새로
생긴 행이 배포본 PL_breakdown.json 과 실제로 일치하는지(단순 재적재인지, 새로운/틀린
값인지) 확인한다 (read-only, 파일 미기록).

usage:
    python scripts/_probes/probe_20260825d_pl_master_regen_diff.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\2e98dd9e-be51-411e-a455-ce573b8bf95c\scratchpad"
)
sys.stdout.reconfigure(encoding="utf-8")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


before = load(SCRATCH / "pl_breakdown_master.json.before")
after = load(ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json")
deployed_before = load(SCRATCH / "PL_breakdown.json.before")


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


b_idx = {key(r): r for r in before}
a_idx = {key(r): r for r in after}
d_idx = {key(r): r for r in deployed_before}

print(f"before rows={len(before)}  after rows={len(after)}  deployed(before)_rows={len(deployed_before)}")

only_in_before = set(b_idx) - set(a_idx)
only_in_after = set(a_idx) - set(b_idx)
print(f"keys only in BEFORE (dropped by regen): {len(only_in_before)}")
print(f"keys NEW in AFTER (not in old intermediate): {len(only_in_after)}")

# Of the keys new in AFTER, how many already existed in the DEPLOYED file (i.e. this
# regen is just catching the intermediate UP to what deployed already had)?
new_matches_deployed = 0
new_not_in_deployed = 0
new_value_mismatch_vs_deployed = []
for k in only_in_after:
    dep = d_idx.get(k)
    if dep is None:
        new_not_in_deployed += 1
        continue
    av, dv = a_idx[k].get("값"), dep.get("값")
    if av is None and dv is None:
        new_matches_deployed += 1
    elif av is not None and dv is not None and abs(av - dv) <= max(0.01, abs(dv) * 1e-6):
        new_matches_deployed += 1
    else:
        new_value_mismatch_vs_deployed.append((k, av, dv))

print(f"  of NEW-in-AFTER: matches deployed(before) value = {new_matches_deployed}")
print(f"  of NEW-in-AFTER: NOT present in deployed(before) at all = {new_not_in_deployed}")
print(f"  of NEW-in-AFTER: value MISMATCH vs deployed(before) = {len(new_value_mismatch_vs_deployed)}")
for k, av, dv in new_value_mismatch_vs_deployed[:30]:
    print("    MISMATCH", k, "after=", av, "deployed_before=", dv)

# Changed values among keys present in BOTH before and after (excluding my intentional
# KR0082 2023.1Q/2Q edits).
changed = []
for k in set(b_idx) & set(a_idx):
    bv, avv = b_idx[k].get("값"), a_idx[k].get("값")
    if bv != avv:
        if not (k[0] == "KR0082" and k[2] in ("2023.1Q", "2023.2Q")):
            changed.append((k, bv, avv))
print(f"\nchanged values among shared keys (excluding my KR0082 2023.1/2Q edits): {len(changed)}")
for k, bv, avv in changed[:60]:
    print("  CHG", k, bv, "->", avv)

print(f"\nonly_in_before (dropped) sample:")
for k in list(only_in_before)[:20]:
    print("  DROPPED", k, b_idx[k].get("값"))
