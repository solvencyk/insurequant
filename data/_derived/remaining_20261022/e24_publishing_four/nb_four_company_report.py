# -*- coding: utf-8 -*-
import json
cur = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/NB_CSM_multiple.json", encoding="utf-8"))
tmp = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e24_publishing_four/nb_rebuilt_tmp.json", encoding="utf-8"))
print("disk == rebuilt:", cur == tmp)
for code in ("KR0099", "KR0003", "KR0070", "KR0009"):
    rows = [r for r in cur if r["원보험사코드"] == code]
    print(code, len(rows), "rows;", "quarters", [r["공시분기"] for r in rows][:3], "...", "NB CSM 연누계 non-null:", sum(1 for r in rows if r.get("신계약CSM_연누계") is not None), "multiple non-null:", sum(1 for r in rows if r.get("신계약CSM배수_연누계") is not None))
