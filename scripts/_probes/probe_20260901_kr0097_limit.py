# -*- coding: utf-8 -*-
"""KR0097 전분기: item48 이 item14전 x 50% 인가 (진짜 한도인가)."""
import json
from pathlib import Path
ROOT=Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
recs=json.loads((ROOT/"kics_disclosure.json").read_text(encoding="utf-8"))
def num(x):
    try: return float(str(x).replace(",",""))
    except: return None
by={}
for r in recs:
    try: it=int(r.get("항목번호"))
    except: continue
    by.setdefault((r.get("원보험사코드"),r.get("공시분기")),{})[it]=num(r.get("값"))
for code in ("KR0097","KR1010"):
    print(f"\n== {code} ==")
    for (c,q),m in sorted(by.items()):
        if c!=code: continue
        i14,i48,i3=m.get(14),m.get(48),m.get(3)
        if i48 is None: print(f"  {q:8s} item48 없음"); continue
        exp = None if i14 is None else i14*0.5
        tag=""
        if exp is not None and abs(i48-exp)<=max(1.0,abs(exp)*0.01): tag="  <= item14x50% 일치(진짜 한도)"
        if i3 is not None and abs(i48-i3)<1e-6: tag+="  *** item48 == item3 (보완자본 복사)"
        print(f"  {q:8s} item14={i14} x50%={exp} | item48={i48} | item3={i3}{tag}")
