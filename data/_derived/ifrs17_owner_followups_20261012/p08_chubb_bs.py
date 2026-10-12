# -*- coding: utf-8 -*-
"""Read-only: IFRS17_BS.json KR0100 rows for items 20/21/22 + overlay/sidecar lineage, and ILP rows items 8,10-15 for KR0100."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
bs = json.loads(open(R + "IFRS17_BS.json", "rb").read().decode("utf-8"))
ov = json.loads(open(R + "data/dart/viz/bs_manual_overrides.json", "rb").read().decode("utf-8"))["cells"]
sd = json.loads(open(R + "data/_derived/bs_from_disclosure.json", "rb").read().decode("utf-8"))["cells"]
qs = ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q","2025.1Q","2025.2Q","2025.3Q","2025.4Q","2026.1Q","2026.2Q"]
idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in bs}
for it in (20, 21, 2):
    print("---- item", it)
    for q in qs:
        r = idx.get(("KR0100", it, q))
        k = f"KR0100|{it}|{q}"
        print(q, r["값"] if r else None, "| overlay:", (ov[k]["값"], ov[k].get("근거","")[:60]) if k in ov else None, "| sidecar:", (sd[k].get("방법"), sd[k].get("pdf"), sd[k].get("page")) if k in sd else None)
ilp = json.loads(open(R + "insurance_liability_portfolio.json", "rb").read().decode("utf-8"))
print("---- ILP KR0100")
by = {}
for r in ilp:
    if r["원보험사코드"] == "KR0100":
        by.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]
for q in qs:
    d = by.get(q, {})
    print(q, {k: d.get(k) for k in (1,2,3,4,5,6,7,8,10,11,12,13,14,15) if k in d})
