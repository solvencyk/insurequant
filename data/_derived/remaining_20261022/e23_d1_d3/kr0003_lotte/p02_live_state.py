# -*- coding: utf-8 -*-
"""Print LIVE master rows for KR0003 (PL + CSM) (read-only)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pl = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
csm = json.load(open(ROOT + "/CSM_waterfall.json", encoding="utf-8"))
SKIP = ("원보험사코드", "원수사명", "공시분기", "항목번호", "항목명", "값", "값_당분기", "생손보여부", "티커")
for label, data in (("PL", pl), ("CSM", csm)):
    rows = [r for r in data if r.get("원보험사코드") == "KR0003"]
    print(label, "KR0003 rows:", len(rows), "quarters:", sorted({r["공시분기"] for r in rows}))
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"):
        rr = [r for r in rows if r["공시분기"] == q]
        rr.sort(key=lambda r: r["항목번호"])
        print("==", label, q, len(rr))
        for r in rr:
            extra = {k: v for k, v in r.items() if k not in SKIP}
            print("  ", r["항목번호"], r["항목명"], "| 값=", r["값"], "| 당분기=", r["값_당분기"], "|", extra if extra else "")
