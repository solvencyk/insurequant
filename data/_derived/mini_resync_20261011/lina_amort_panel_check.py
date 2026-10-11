# -*- coding: utf-8 -*-
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2].parent
p = json.loads((ROOT / "data/dart/viz/csm_amort_schedule.json").read_text(encoding="utf-8"))
for c in p["companies"]:
    if "라이나" in c["company"]:
        print({k: c.get(k) for k in ("company", "status", "period", "as_of", "unit", "buckets", "yearly", "_source", "rcept_no")})
print("not ok:", [(c["company"], c.get("status")) for c in p["companies"] if c.get("status") != "ok"])
m = json.loads((ROOT / "CSM_amortization.json").read_text(encoding="utf-8"))
qs = sorted({r["공시분기"] for r in m if r["원보험사코드"] == "KR0074"})
print("Lina master amort quarters:", qs)
for r in m:
    if r["원보험사코드"] == "KR0074" and r["공시분기"] == qs[-1]:
        print(r["경과차년"], r["상각액"])
