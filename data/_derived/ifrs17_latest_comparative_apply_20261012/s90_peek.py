"""Peek helper: verdict distribution of the dry-run census and the block structure of plan_final.json (read-only)."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DR = ROOT / "data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012"

rows = list(csv.DictReader(open(DR / "census_blocks.csv", encoding="utf-8-sig")))
print("census blocks:", len(rows))
print(Counter(r["verdict"] for r in rows))
print(Counter((r["domain"], r["verdict"]) for r in rows))
plan = json.loads((HERE / "plan_final.json").read_text(encoding="utf-8"))
print("plan keys:", list(plan.keys()))
print("cells:", len(plan["cells"]))
c0 = plan["cells"][0]
print("cell keys:", list(c0.keys()))
print(json.dumps(c0, ensure_ascii=False)[:600])
for k in plan:
    if k != "cells":
        v = plan[k]
        print(k, type(v).__name__, (list(v)[:3] if hasattr(v, "__iter__") else v))
blocks = Counter((c["master"], c["code"], c["quarter"], c.get("kind")) for c in plan["cells"])
print("distinct (master,code,quarter,kind):", len(blocks))
print(Counter(c.get("kind") for c in plan["cells"]))
