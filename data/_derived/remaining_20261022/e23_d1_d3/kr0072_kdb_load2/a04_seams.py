# -*- coding: utf-8 -*-
"""read-only: the single-quarter seam table of the regenerated plan, grouped by class, and the Q4 vintage evidence per touched Q4 cell."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / "e23_plan_kdb_final.json").read_text(encoding="utf-8"))
by = defaultdict(list)
for s in plan["seams"]:
    by[s["cls"]].append(s)
for cls, lst in sorted(by.items()):
    print(f"== {cls}: {len(lst)} cells")
    for s in sorted(lst, key=lambda x: (x["quarter"], x["item"])):
        extra = ""
        if s.get("printed_3m"):
            extra = f" printed3m {s['printed_3m']['value']} diff_vs_printed_3m {s.get('diff_vs_printed_3m')}"
        if s["quarter"] == "2023.4Q":
            extra += f" | cur_adopted {s['cur_adopted']} prev_adopted {s['prev_adopted']} q3_restated {s.get('q3_restated')} q3_evidence {s.get('q3_evidence')} q4_comp_vs_master {s.get('q4_comp_vs_master')}"
        print(f"   {s['quarter']} i{s['item']:>2}: derived_after {s['derived_after']} live_dangi {s['live_dangi']} proposal {s['proposal']}{extra}")
C = plan["apply_contract"]
print("null_dangi_add:", C["null_dangi_add"], "| null_dangi_remove:", C["null_dangi_remove"])
print("set_dangi_add:", len(C["set_dangi_add"]), "| set_dangi_remove:", C["set_dangi_remove"])
