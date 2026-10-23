# -*- coding: utf-8 -*-
"""read-only: the plan regenerated today against the LIVE tree (kr0072_kdb_load2/e23_plan_kdb_final.json) vs the plan made before the hold (kr0072_kdb/e23_plan_kdb_final.json).
The only expected differences are the evidence-folder name inside note strings and the generation time stamp."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
OLD = json.loads((HERE.parent / "kr0072_kdb" / "e23_plan_kdb_final.json").read_text(encoding="utf-8"))
NEW = json.loads((HERE / "e23_plan_kdb_final.json").read_text(encoding="utf-8"))


def norm(o):
    if isinstance(o, str):
        return o.replace("kr0072_kdb_load2", "kr0072_kdb")
    if isinstance(o, list):
        return [norm(x) for x in o]
    if isinstance(o, dict):
        return {k: norm(v) for k, v in o.items() if k != "generated"}
    return o


a, b = norm(OLD), norm(NEW)
diffs = []


def walk(x, y, path):
    if type(x) is not type(y):
        diffs.append((path, "type", str(x)[:80], str(y)[:80]))
        return
    if isinstance(x, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x or k not in y:
                diffs.append((path + "/" + k, "missing", k in x, k in y))
            else:
                walk(x[k], y[k], path + "/" + k)
    elif isinstance(x, list):
        if len(x) != len(y):
            diffs.append((path, "len", len(x), len(y)))
            return
        for i, (p, q) in enumerate(zip(x, y)):
            walk(p, q, f"{path}[{i}]")
    elif x != y:
        diffs.append((path, "value", str(x)[:120], str(y)[:120]))


walk(a, b, "")
print("differences after normalising the evidence-folder name and the time stamp:", len(diffs))
for d in diffs[:40]:
    print("  ", d)
C = NEW["apply_contract"]
print("contract counts:", {k: len(v) for k, v in C.items()})
print("n_pl_cells", NEW["n_pl_cells"], "n_csm_cells", NEW["n_csm_cells"])
