# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
ilp = json.loads(open(R + "insurance_liability_portfolio.json", "rb").read().decode("utf-8"))
prov = json.loads(open(R + "insurance_liability_portfolio_provenance.json", "rb").read().decode("utf-8"))
bs = json.loads(open(R + "IFRS17_BS.json", "rb").read().decode("utf-8"))
for q in ("2023.4Q", "2024.4Q", "2025.4Q"):
    vals = {r["항목번호"]: r["값"] for r in ilp if r["원보험사코드"] == "KR0029" and r["공시분기"] == q}
    print(q, vals, "| BS20", [r["값"] for r in bs if r["원보험사코드"] == "KR0029" and r["항목번호"] == 20 and r["공시분기"] == q])
for sect in ("cells", "lrc_model_cells", "lrc_model_not_loaded", "not_loaded"):
    for c in prov.get(sect, []):
        if c.get("company_code") == "KR0029" and c.get("quarter") in ("2024.4Q",):
            print("=" * 80, sect)
            print(json.dumps(c, ensure_ascii=False, indent=1)[:3500])
