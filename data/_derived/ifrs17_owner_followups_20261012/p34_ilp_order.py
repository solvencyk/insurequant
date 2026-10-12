# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = json.loads(open("C:/Users/sangwook.cho/Desktop/insurequant/insurance_liability_portfolio.json", "rb").read().decode("utf-8"))
# positions of KR1102 rows grouped by (quarter) with item ranges
last = None
for i, r in enumerate(rows):
    if r["원보험사코드"] == "KR1102":
        k = (r["공시분기"], r["항목번호"] <= 9)
        if k != last:
            print(i, r["공시분기"], r["항목번호"])
            last = k
# global ordering check for the first block (items <=9): sorted by code, quarter, item?
blk1 = [(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in rows if r["항목번호"] <= 9]
print("block1 len", len(blk1), "sorted by (code, quarter, item):", blk1 == sorted(blk1))
blk2 = [(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in rows if r["항목번호"] >= 10]
print("block2 len", len(blk2), "sorted:", blk2 == sorted(blk2))
# where does block1 end
idx_first_ge10 = next(i for i, r in enumerate(rows) if r["항목번호"] >= 10)
print("first item>=10 at", idx_first_ge10, "last item<=9 at", max(i for i, r in enumerate(rows) if r["항목번호"] <= 9))
# sample ordering around KR1102 2025.4Q / 2026.2Q
for i, r in enumerate(rows):
    if r["원보험사코드"] == "KR1102" and r["공시분기"] == "2026.2Q" and r["항목번호"] in (1, 8):
        print(i, json.dumps(r, ensure_ascii=False))
