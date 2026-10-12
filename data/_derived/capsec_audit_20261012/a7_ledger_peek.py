# -*- coding: utf-8 -*-
"""a7: peek at the per-bond ledger (data/bonds/capital_securities_fy2026h1.json) (read-only)."""
import json

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
doc = json.load(open(ROOT + "/data/bonds/capital_securities_fy2026h1.json", encoding="utf-8"))
print("top keys", list(doc.keys()))
for k, v in doc.items():
    if k != "companies":
        print(k, ":", str(v)[:300])
cs = doc["companies"]
print("n companies", len(cs))
print("company keys", list(cs[0].keys()))
print("bond keys", list(cs[0]["bonds"][0].keys()) if cs[0].get("bonds") else None)
for c in cs:
    if c["code"] in ("KR0079", "KR0082", "KR0068"):
        print("==", c["code"], c.get("name"), "as_of", c.get("as_of"))
        for b in c["bonds"]:
            print("  ", {k: b.get(k) for k in ("name", "tier", "issue_date", "call_date", "legal_maturity", "face_amount_mn", "outstanding_mn", "past_call_outstanding", "status", "as_of")})
