# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
plan = json.loads((Path(__file__).resolve().parent / "e23_plan_kdb.json").read_text(encoding="utf-8"))
cb = plan["csm_buckets"][0]
print({k: v for k, v in cb.items() if k not in ("cells",)})
print(json.dumps(cb["cells"][0], ensure_ascii=False, indent=1))
print(json.dumps(cb["cells"][2], ensure_ascii=False, indent=1))
b = plan["buckets"][0]
print({k: v for k, v in b.items() if k not in ("cells", "dropped", "closure")})
print(json.dumps(plan["buckets"][3]["cells"][2], ensure_ascii=False, indent=1)[:1800])
print(json.dumps(plan["apply_contract"]["gold_replace"][0], ensure_ascii=False, indent=1)[:3500])
print(json.dumps(plan["apply_contract"]["csm_gold_replace"][0], ensure_ascii=False, indent=1)[:2500])
print(json.dumps(plan["apply_contract"]["set_dangi_add"][2], ensure_ascii=False)[:1200])
print(json.dumps(plan["csm_gold_class"], ensure_ascii=False)[:1500])
