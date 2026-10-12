# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
wf = json.loads(open(R + "CSM_waterfall.json", "rb").read().decode("utf-8"))
for r in wf:
    if r["원보험사코드"] == "KR0004":
        print("WF", r["공시분기"], r["항목번호"], r["항목명"], r["값"], r.get("값_당분기"))
prov = json.loads(open(R + "CSM_waterfall_provenance.json", "rb").read().decode("utf-8"))
for c in prov["cells"]:
    if c["company_code"] == "KR0004":
        print("PROV", c)
ilp = json.loads(open(R + "insurance_liability_portfolio.json", "rb").read().decode("utf-8"))
for q in ("2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"):
    vals = {r["항목번호"]: r["값"] for r in ilp if r["원보험사코드"] == "KR0004" and r["공시분기"] == q}
    print("ILP", q, vals)
pv = json.loads(open(R + "insurance_liability_portfolio_provenance.json", "rb").read().decode("utf-8"))
for sect in ("lrc_model_cells", "cells", "not_loaded", "lrc_model_not_loaded"):
    for c in pv.get(sect, []):
        if c.get("company_code") == "KR0004" and c.get("quarter") in ("2025.4Q", "2025.3Q"):
            print("=" * 60, sect, c["quarter"])
            print(json.dumps(c, ensure_ascii=False)[:1800])
