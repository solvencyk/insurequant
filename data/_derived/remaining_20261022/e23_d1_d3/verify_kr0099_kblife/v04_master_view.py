# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
pl=json.load(open(R+"PL_breakdown.json",encoding="utf-8"))
rows=[r for r in pl if r["원보험사코드"]=="KR0099"]
names={}
for r in rows: names[r["항목번호"]]=r["항목명"]
qs=["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q"]
d={(r["항목번호"],r["공시분기"]):(r["값"],r["값_당분기"]) for r in rows}
print("item name | "+" | ".join(qs))
for i in sorted(names):
    print(i,names[i],"|"," | ".join(str(d.get((i,q))) for q in qs))
cs=json.load(open(R+"CSM_waterfall.json",encoding="utf-8"))
rows=[r for r in cs if r["원보험사코드"]=="KR0099"]
names={r["항목번호"]:r["항목명"] for r in rows}
d={(r["항목번호"],r["공시분기"]):(r["값"],r["값_당분기"]) for r in rows}
qs=["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"]
for i in sorted(names):
    print("CSM",i,names[i],"|"," | ".join(str(d.get((i,q))) for q in qs))
