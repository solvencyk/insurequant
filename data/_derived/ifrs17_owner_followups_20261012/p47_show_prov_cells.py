# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(R + "insurance_liability_portfolio_provenance.json", "rb").read().decode("utf-8"))
for c in d["cells"]:
    if c["company_code"] == "KR0100" and c["quarter"] in ("2024.1Q", "2025.3Q"):
        print(json.dumps({k: v for k, v in c.items() if k not in ("tables", "dropped_tables", "dedupe")}, ensure_ascii=False, indent=1)[:3500])
        print("=" * 80)
print(json.dumps(d["value_corrections"][-1], ensure_ascii=False, indent=1))
print(json.dumps(d["backfills"][-1], ensure_ascii=False, indent=1))
