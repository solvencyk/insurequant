# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.load(open("kics_disclosure.json", encoding="utf-8"))
rows = [r for r in data if r.get("원보험사코드")=="KR0076" and r.get("공시분기")=="2026.2Q"]
by_item = {r["항목번호"]: r for r in rows}

for it in (16, 18, 23):
    r = by_item[it]
    print(json.dumps({k: r[k] for k in ("원보험사코드","원수사명","티커","생손보여부","항목번호","항목명","공시분기","값")}, ensure_ascii=False))

# also grab item41-46 항목명 from a historical KR0076 even-quarter row (2026.1Q doesn't have it since odd; use 2025.4Q)
data_all = data
hist = [r for r in data_all if r.get("원보험사코드")=="KR0076" and r.get("공시분기")=="2025.4Q" and r.get("항목번호") in range(41,47)]
hist.sort(key=lambda r: r["항목번호"])
print("---item41-46 labels from 2025.4Q precedent---")
for r in hist:
    print(json.dumps({"항목번호": r["항목번호"], "항목명": r["항목명"]}, ensure_ascii=False))
