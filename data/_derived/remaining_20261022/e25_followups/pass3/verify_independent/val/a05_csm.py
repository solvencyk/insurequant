# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/CSM_waterfall.json", encoding="utf-8"))
names = {}
for r in d:
    names[str(r["항목번호"])] = r.get("항목명")
print({k: names[k] for k in sorted(names, key=lambda x: (len(x), x))})
rows = [r for r in d if r["원보험사코드"]=="KR0087"]
print(sorted({r["공시분기"] for r in rows}))
print(set(rows[0]))
