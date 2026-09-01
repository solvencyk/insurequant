# -*- coding: utf-8 -*-
import json, pathlib
from collections import defaultdict
ROOT = pathlib.Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
recs = json.loads((ROOT/"kics_disclosure.json").read_text(encoding="utf-8"))
def f(v):
    if v is None: return None
    s=str(v).replace(",","").replace("△","-").strip()
    if s in ("","-","None"): return None
    try: return float(s)
    except ValueError: return None
pre=defaultdict(dict); post=defaultdict(dict); nm={}
for r in recs:
    k=(r["원보험사코드"], r["공시분기"]); nm[r["원보험사코드"]]=r["원수사명"]
    pre[k][r["항목번호"]]=f(r.get("값")); post[k][r["항목번호"]]=f(r.get("값_적용후"))
CH=[24,25,26]
rows=[]
for k in sorted(pre):
    p23=post[k].get(23)
    if p23 is None: continue
    have=[c for c in CH if post[k].get(c) is not None]
    if have: continue                     # 자식이 하나라도 있으면 대상 아님
    prehave=[c for c in CH if pre[k].get(c) is not None]
    same = pre[k].get(23) is not None and abs(p23-pre[k][23])<=0.5
    rows.append((k[0], nm[k[0]], k[1], p23, len(prehave), same))
print("적용후 item23 있는데 자식 24-26 전부 결측: %d 버킷" % len(rows))
by=defaultdict(list)
for c,n,q,v,ph,same in rows: by[(c,n)].append((q,v,ph,same))
for (c,n),v in sorted(by.items(), key=lambda x:-len(x[1])):
    qs=", ".join(q for q,_,_,_ in v)
    nsame=sum(1 for _,_,_,s in v if s); nprech=sum(1 for _,_,p,_ in v if p)
    print(f"  {c} {n:12s} {len(v):2d}건  후==전 {nsame}건 · 적용전자식보유 {nprech}건")
    print(f"      {qs}")
