# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(R + "insurance_liability_portfolio_provenance.json", "rb").read().decode("utf-8"))
for k in ("value_corrections", "backfills"):
    v = d[k]
    print("=" * 80, k, len(v))
    for rec in v[:2]:
        print(json.dumps(rec, ensure_ascii=False, indent=1)[:1500])
print("note:", str(d["note"])[:600])
print("inputs:", json.dumps(d["inputs"], ensure_ascii=False)[:600])
print("generated_at:", d["generated_at"], d["emitter"], d["emitted_by"] if "emitted_by" in d else None)
raw = open(R + "insurance_liability_portfolio.json", "rb").read()
print("ILP master bytes", len(raw), "CRLF" if b"\r\n" in raw else "LF", "endsNL" if raw.endswith(b"\n") else "noEndNL")
