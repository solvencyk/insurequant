# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = json.loads(open("e23_plan_kblife.json", encoding="utf-8").read())
for b in p["buckets"]:
    print("==", b["quarter"], "closure_ok", b["closure_ok"], "cells", len(b["cells"]))
    for c in b["cells"]:
        parts = "; ".join(f"L{x['line']} {x['printed']}{'(abs)' if x.get('abs') else ''}" for x in c["parts"])
        ops = ",".join(f"{o['item']}={o['value']}({o['source']})" for o in c["operands"])
        print(f"  i{c['item']:>2} {c['item_name']:<14} old={c['old']} new={c['new']} d={c['delta']} [{c['cls']}] cand={c['cand_new']} | {parts} | ops {ops}")
for cb in p["csm_buckets"]:
    print("== CSM", cb["quarter"], "resid", cb["closure_resid"], "src", cb["src"])
    for c in cb["cells"]:
        parts = "; ".join(f"L{x['line']} {x['printed']}" for x in c["parts"])
        print(f"  i{c['item']} {c['item_name']} old={c['old']} new={c['new']} exact={c['exact']} | {parts}")
