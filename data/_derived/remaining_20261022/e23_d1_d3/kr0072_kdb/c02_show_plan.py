# -*- coding: utf-8 -*-
"""read-only: compact view of e23_plan_kdb.json (cells, dropped, CSM cells, contract)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / (sys.argv[1] if len(sys.argv) > 1 else "e23_plan_kdb.json")).read_text(encoding="utf-8"))
print("keys:", list(plan.keys()))
for b in plan["buckets"]:
    print(f"== {b['code']} {b['quarter']} file {b['meta']['file']} unit {b['meta']['unit']} cells {len(b['cells'])}")
    for c in b["cells"]:
        parts = "; ".join(f"L{p.get('line')}:{p.get('label','')[:22]}:{p.get('printed')}" for p in c["parts"][:4])
        print(f"   i{c['item']:>2} {c['item_name'][:14]:14s} old {c['old']} new {c['new']} delta {c['delta']} cand {c['cand_new']} gold {c['gold_cell']} cls {c['cls']} | {c['kind']} | {parts}")
    for d in b["dropped"]:
        print(f"   DROPPED i{d['item']}: old {d['old']} new {d['new']} cls {d['cls']} reason {d['reason']}")
print()
for cb in plan["csm_buckets"]:
    print(f"== CSM {cb['code']} {cb['quarter']} 2dp {cb['two_dp']} file {cb['file']}")
    print("   exact", cb["vec_exact"], "stored", cb["vec"], "old", cb["old"], "closure_resid", cb["closure_resid"])
    for c in cb["cells"]:
        print(f"   i{c['item']} {c['item_name']}: old {c['old']} new {c['new']} delta {c['delta']} exact {c['exact']} cand {c['cand_new']} gold {c['gold_cell']} | {[(p.get('line'), p.get('printed')) for p in c['parts']]}")
C = plan["apply_contract"]
print()
for k, v in C.items():
    print(k, len(v))
print("seams (non-trivial):")
for s in plan["seams"]:
    if s["proposal"] != "none" or s["cls"] not in ("consistent", "lob_item_not_checked_directly", "q4_unchanged_q3_adopted"):
        print("  ", s["quarter"], "i", s["item"], s["cls"], s["proposal"], "D", s["derived_after"], "printed3m", (s.get("printed_3m") or {}).get("value"), "live_dangi", s["live_dangi"])
print("findings:", plan["findings"])
