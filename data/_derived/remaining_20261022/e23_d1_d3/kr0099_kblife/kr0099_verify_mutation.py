# -*- coding: utf-8 -*-
"""sensitivity test of kr0099_verify.py: mutate the cited line numbers / values of a copy of the plan; the verifier must FAIL on every mutation (exit 1)."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.stdout.reconfigure(encoding="utf-8")
base = json.loads((HERE / "e23_plan_kblife.json").read_text(encoding="utf-8"))
plan = base


def cell(q, item):
    for b in plan["buckets"]:
        if b["quarter"] == q:
            for c in b["cells"]:
                if c["item"] == item:
                    return c


def csmcell(q, item):
    for cb in plan["csm_buckets"]:
        if cb["quarter"] == q:
            for c in cb["cells"]:
                if c["item"] == item:
                    return c


MUTS = []
# 1 statement cell moved to the prior 3-month column (-4 lines)
MUTS.append(("stmt 2023.3Q i22 line-4 (prior 3m column)", lambda p: cell("2023.3Q", 22)["parts"][0].__setitem__("line", cell("2023.3Q", 22)["parts"][0]["line"] - 4)))
# 2 statement cell moved to the current cumulative column (-8)
MUTS.append(("stmt 2023.2Q i24 line-8 (current cum column)", lambda p: cell("2023.2Q", 24)["parts"][0].__setitem__("line", cell("2023.2Q", 24)["parts"][0]["line"] - 8)))
# 3 PL4 cited cell moved to the 3-month 합계 column
MUTS.append(("pl4 2023.2Q line-6 (3-month 합계 column)", lambda p: cell("2023.2Q", 4)["parts"][0].__setitem__("line", cell("2023.2Q", 4)["parts"][0]["line"] - 6)))
# 4 CSM cell moved to the 위험조정 column
MUTS.append(("csm 2023.1Q item 5 line-1 (위험조정 column)", lambda p: csmcell("2023.1Q", 5)["parts"][0].__setitem__("line", csmcell("2023.1Q", 5)["parts"][0]["line"] - 2)))
# 5 value mutated
MUTS.append(("value 2023.1Q i17 +1", lambda p: cell("2023.1Q", 17).__setitem__("new", cell("2023.1Q", 17)["new"] + 1)))
# 6 wrong label occurrence (rev: 2nd 보험영업수익 -> 1st, line of row 7)
MUTS.append(("item 3 2023.1Q rev line of the total row", lambda p: cell("2023.1Q", 3)["parts"][0].__setitem__("line", 25504)))
# 7 consolidated statement instead of separate: shift into the consolidated 2-2 statement is not addressable by a small offset; skip -> use old mismatch
MUTS.append(("old != HEAD (2023.3Q i22 old +5)", lambda p: cell("2023.3Q", 22).__setitem__("old", cell("2023.3Q", 22)["old"] + 5)))
fails = 0
for k, (name, fn) in enumerate(MUTS):
    p = copy.deepcopy(base)
    globals()["plan"] = p
    fn(p)
    tmp = HERE / f"_mut_plan_{k}.json"
    tmp.write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8", newline="\n")
    env = dict(os.environ, KR0099_PLAN=tmp.name, KR0099_OUTTAG=f"_mut{k}", PYTHONIOENCODING="utf-8")
    r = subprocess.run([PY, str(HERE / "kr0099_verify.py")], cwd=str(HERE), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    ok = r.returncode == 1
    out = json.loads((HERE / f"kr0099_verify_mut{k}.json").read_text(encoding="utf-8"))
    print(f"mutation {k} [{name}]: verifier exit {r.returncode} -> {'DETECTED' if ok else 'MISSED'}; first problem: {out['problems'][0]['problem'][:150] if out['problems'] else None}")
    fails += 0 if ok else 1
    tmp.unlink()
    (HERE / f"kr0099_verify_mut{k}.txt").unlink()
    (HERE / f"kr0099_verify_mut{k}.json").unlink()
print("mutations missed:", fails)
sys.exit(1 if fails else 0)
