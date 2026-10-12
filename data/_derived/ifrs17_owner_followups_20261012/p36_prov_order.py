# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
prov = json.loads(open(R + "insurance_liability_portfolio_provenance.json", "rb").read().decode("utf-8"))
lm = prov["lrc_model_cells"]
print("lrc_model_cells", len(lm))
print("last 6:", [(c["company_code"], c["quarter"]) for c in lm[-6:]])
print("KR1102:", [(i, c["quarter"]) for i, c in enumerate(lm) if c["company_code"] == "KR1102"])
nl = prov["lrc_model_not_loaded"]
print("lrc_model_not_loaded", len(nl), [(c["company_code"], c["quarter"]) for c in nl if c["company_code"] in ("KR1102", "KR1104")])
print("keys of a not_loaded:", list(nl[0].keys()))
print("backfills tail:", [b.get("stage") for b in prov["backfills"][-4:]])
# the exact record for KR1102 2026.1Q
for c in nl:
    if c["company_code"] == "KR1102" and c["quarter"] == "2026.1Q":
        print(json.dumps(c, ensure_ascii=False)[:2000])
