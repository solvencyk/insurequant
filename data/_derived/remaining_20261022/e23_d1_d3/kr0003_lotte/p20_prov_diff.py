# -*- coding: utf-8 -*-
"""Read-only: show the KR0003 2023.4Q provenance blocks before (backup) and after (live), field-level diff, plus the CSM provenance block."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
BK = ROOT + "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0003_lotte/"
def blocks(path):
    d = json.load(open(path, encoding="utf-8"))
    return {(c["company_code"], c["quarter"], c["item_block"]): c for c in d["cells"]}, d
b0, d0 = blocks(BK + "PL_breakdown_provenance.json")
b1, d1 = blocks(ROOT + "PL_breakdown_provenance.json")
for k in sorted(b1):
    if b0.get(k) != b1[k]:
        print("== PL block", k)
        a, b = b0.get(k, {}), b1[k]
        for f in sorted(set(a) | set(b)):
            if a.get(f) != b.get(f):
                sa, sb = json.dumps(a.get(f), ensure_ascii=False), json.dumps(b.get(f), ensure_ascii=False)
                print(f"   {f}:\n      before: {sa[:420]}\n      after : {sb[:420]}")
c0, e0 = blocks(BK + "CSM_waterfall_provenance.json")
c1, e1 = blocks(ROOT + "CSM_waterfall_provenance.json")
for k in sorted(c1):
    if c0.get(k) != c1[k]:
        print("== CSM block", k)
        for f in sorted(set(c0[k]) | set(c1[k])):
            if c0[k].get(f) != c1[k].get(f):
                print(f"   {f}: {json.dumps(c0[k].get(f), ensure_ascii=False)[:200]} -> {json.dumps(c1[k].get(f), ensure_ascii=False)[:200]}")
print("merge notes:", [k for k in d1 if k.startswith("merge_note") and k not in d0], [k for k in e1 if k.startswith("merge_note") and k not in e0])
