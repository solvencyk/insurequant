# -*- coding: utf-8 -*-
"""8_life 전수: (a) KR0069 전분기 잔차 (b) SKIP 사유 census — 어떤 항목이 없어서 안 보고 있나."""
import json, sys, collections
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT))
import src.solvency.validation.kics_json_rules as K
recs = json.loads((ROOT/"kics_disclosure.json").read_text(encoding="utf-8"))
if isinstance(recs, dict): recs = recs.get("records") or recs.get("data") or []
def num(x):
    try: return float(str(x).replace(",",""))
    except: return None
by = {}
name={}
for r in recs:
    c,q = r.get("원보험사코드"), r.get("공시분기")
    name[c]=r.get("원수사명")
    try: it=int(r.get("항목번호"))
    except: continue
    by.setdefault((c,q),{})[it]=(num(r.get("값")), num(r.get("값_적용후")))

print("== KR0069 삼성생명 전분기 8_life ==")
for (c,q),m in sorted(by.items()):
    if c!="KR0069": continue
    g=lambda i: (m.get(i) or (None,None))[0]
    subs=[g(i) for i in range(29,36)]
    i17=g(17)
    if i17 is None or any(s is None for s in subs):
        print(f"  {q:8s} SKIP  item17={i17} 결측={[i for i in range(29,36) if g(i) is None]}")
        continue
    exp=K._diversified_sqrt(subs, K.R7)
    tol=max(0.0, K.DIVERSIFIED_SQRT_TOL_REL*abs(exp))
    print(f"  {q:8s} exp={exp:12,.2f} item17={i17:12,.2f} diff={i17-exp:+10,.2f} tol={tol:9,.2f} {'PASS' if abs(i17-exp)<=tol else '*** FAIL'}")

print("\n== 전수 8_life SKIP 사유 census (적용전) ==")
cnt=collections.Counter(); miss=collections.Counter(); skips=[]
for (c,q),m in sorted(by.items()):
    g=lambda i: (m.get(i) or (None,None))[0]
    subs_missing=[i for i in range(29,36) if g(i) is None]
    if g(17) is None and subs_missing: cnt["17+세부 모두결측"]+=1; continue
    if g(17) is None: cnt["item17만 결측"]+=1; continue
    if not subs_missing: cnt["평가됨"]+=1; continue
    cnt["세부 부분결측 -> SKIP"]+=1
    miss[tuple(subs_missing)]+=1
    skips.append((c,name.get(c),q,subs_missing))
for k,v in cnt.most_common(): print(f"   {k:26s} {v}")
print("\n   부분결측 패턴 top:")
for pat,n in miss.most_common(8): print(f"     결측={list(pat)}  {n}건")
print("\n   ** 오직 item32 만 결측(=0 하나 넣으면 평가 개시)인 버킷:")
only32=[s for s in skips if s[3]==[32]]
for c,nm,q,_ in only32: print(f"     {c} {nm} {q}")
print(f"     합계 {len(only32)}건")
