# -*- coding: utf-8 -*-
"""정정안 v2 — KR0097 2024.4Q 는 47-51 추가 대신 item48/52 제거(원문에 TFI표 없음)."""
import json, os, collections
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
SCRATCH = Path(os.environ["SCRATCH"])
recs = json.loads((ROOT/"kics_disclosure.json").read_text(encoding="utf-8"))
before = len(recs)
def find(code,q,item):
    for r in recs:
        if r.get("원보험사코드")==code and r.get("공시분기")==q and str(r.get("항목번호"))==str(item): return r
find("KR0080","2024.3Q",13)["값"]="6327"
B={29:"18589.38",30:"23332.41",31:"46106.95",32:"0",33:"68322.65",34:"21101.73",35:"7142.45"}
for it,v in B.items():
    r=find("KR0069","2024.4Q",it)
    r["값"]=v
    if r.get("값_적용후") is not None: r["값_적용후"]=v
kill=set(); removed=[]
for code,qs in (("KR1010",("2023.2Q","2023.3Q")), ("KR0097",("2024.4Q",))):
    for q in qs:
        for it in (48,52):
            r=find(code,q,it)
            if r is not None: kill.add(id(r)); removed.append((code,q,it,r.get("값")))
recs=[r for r in recs if id(r) not in kill]
print("removed:", removed)
print(f"rows {before} -> {len(recs)} (기대 -{len(removed)})")
dups=[k for k,v in collections.Counter((r.get("원보험사코드"),r.get("공시분기"),str(r.get("항목번호"))) for r in recs).items() if v>1]
print("중복 콤보:", len(dups))
out=SCRATCH/"kics_disclosure_SIM2.json"
out.write_text(json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", out)
