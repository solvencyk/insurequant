# -*- coding: utf-8 -*-
"""read-only: print the ABL plan cells with citations"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / (sys.argv[1] if len(sys.argv) > 1 else "e23_plan_abl.json")).read_text(encoding="utf-8"))
print("keys", list(plan.keys()))
for b in plan["buckets"]:
    m = b["meta"]
    print("=" * 100)
    print(b["quarter"], b["kind"], m["file"], "unit", m["unit"], "role", m.get("role"), "fmt", m.get("fmt"))
    for c in b["cells"]:
        print(f"  i{c['item']:>2} {c['item_name']}: old={c['old']} new={c['new']} delta={c['delta']} kind={c['kind']} formula={c['formula']!r} gold={c['gold_cell']}")
        for p in c["parts"]:
            print(f"        part L{p.get('line')} {p.get('label')!r} printed={p.get('printed')} sign={p.get('sign')} abs={p.get('abs')} unit={p.get('unit')} contrib={p.get('contribution_mn')}")
        for o in c["operands"]:
            print(f"        operand {o}")
    for d in b["dropped"]:
        print("  dropped", d)
print("=" * 100)
for cb in plan["csm_buckets"]:
    print(cb["quarter"], cb["file"], "vec_exact", cb["vec_exact"], "vec", cb["vec"], "old", cb["old"], "closure", cb["closure_resid"], "group_row_amort", cb.get("group_row_amort"))
    for c in cb["cells"]:
        print(f"  csm i{c['item']} {c['item_name']}: old={c['old']} new={c['new']} exact={c['exact']} derived={c['derived']}")
        for p in c["parts"]:
            print("        part", p)
    for d in cb["dropped"]:
        print("  dropped", d)
print(json.dumps(plan["apply_contract"]["gold_replace"], ensure_ascii=False, indent=1)[:3000])
