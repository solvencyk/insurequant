# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
plan = json.load(open("e23_plan_lotte.json", encoding="utf-8"))
print("top keys:", list(plan.keys()))
for b in plan["buckets"]:
    print("== bucket", b["code"], b["quarter"], b["kind"], "closure_ok", b["closure_ok"])
    print("   meta:", json.dumps(b["meta"], ensure_ascii=False))
    for c in b["cells"]:
        print(f"-- item {c['item']} {c['item_name']}: old {c['old']} -> new {c['new']} (delta {c['delta']}) cand_new {c['cand_new']} formula: {c['formula']}")
        for p in c["parts"]:
            print("     part:", json.dumps({k: p[k] for k in p if k in ("label", "line", "printed", "sign", "abs", "unit", "contribution_mn", "xlsx", "cell")}, ensure_ascii=False))
        if c["operands"]:
            print("     operands:", json.dumps(c["operands"], ensure_ascii=False))
    print("   dropped:", json.dumps(b["dropped"], ensure_ascii=False))
print("== csm buckets")
for cb in plan["csm_buckets"]:
    print(json.dumps({k: cb[k] for k in cb if k != "cells"}, ensure_ascii=False)[:1500])
    for c in cb["cells"]:
        print(f"-- CSM item {c['item']} {c['item_name']}: old {c['old']} -> new {c['new']} exact {c['exact']} derived {c.get('derived')} src {c['src']}")
        for p in c["parts"]:
            print("     part:", json.dumps(p, ensure_ascii=False)[:400])
