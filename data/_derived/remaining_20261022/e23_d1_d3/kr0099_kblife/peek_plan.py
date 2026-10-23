# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = json.loads(open("e23_plan_kblife.json", encoding="utf-8").read())
print(list(p.keys()))
c = p["apply_contract"]
print({k: len(v) for k, v in c.items()})
print(json.dumps(c["gold_new"][0], ensure_ascii=False, indent=1))
print(json.dumps(c["gold_new"][5], ensure_ascii=False, indent=1))
print(json.dumps(c["csm_gold_new"][0], ensure_ascii=False, indent=1))
b = p["buckets"][0]
print(list(b.keys()))
print(json.dumps(b["cells"][5], ensure_ascii=False, indent=1)[:2500])
