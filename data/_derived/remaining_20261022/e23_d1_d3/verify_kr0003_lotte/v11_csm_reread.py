# -*- coding: utf-8 -*-
import sys, json, subprocess
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte")
from vlib import *
from decimal import Decimal, ROUND_HALF_UP
sys.stdout.reconfigure(encoding="utf-8")
L=[]
def Pp(*a):
    s=" ".join(str(x) for x in a); L.append(s); print(s)
def cands(txt):
    out=[]
    for T in tables(txt):
        labs=[re.sub(r"\s+","",r[0]["t"]) for r in T["rows"] if r]
        hdr=" ".join(c["t"] for r in T["rows"][:4] for c in r)
        if "기초순보험계약부채" in labs and "보험계약마진상각액" in labs and "소계" in re.sub(r"\s+","",hdr) and "최초인식계약" in labs:
            out.append(T)
    return out
def vec(T):
    """return dict of CSM 소계 column values in 백만원 with line numbers: second-to-last numeric col (before 합 계)"""
    d={}
    for r in T["rows"]:
        if len(r)<3: continue
        lab=re.sub(r"\s+","",r[0]["t"])
        v=[(num(c["t"]),c["line"]) for c in r[1:] if num(c["t"]) not in (None,"NaN") or c["t"].strip() in ("-",)]
        vals=[(0.0 if x is None else x,l) for x,l in v]
        if len(vals)>=7:
            d.setdefault(lab,vals[-2])   # CSM 소계 = column before 합계
    return d
def eok(x):  # 백만원 -> 억원 rounded half-up 1 decimal
    return float((Decimal(str(x))/Decimal(100)).quantize(Decimal("0.1"),rounding=ROUND_HALF_UP))
def eok_exact(x): return x/100.0
txtN=load(NEW); txtO=load(ORIG)
cN=cands(txtN); cO=cands(txtO)
Pp("NEW candidates lines",[t["line"] for t in cN],"; ORIG candidates",[t["line"] for t in cO])
# pick prior (second) of NEW pair & current (first) of ORIG pair
TN=[t for t in cN if t["line"]==19837][0]; TO=cO[0]
Pp("NEW table used L%d (marker before table = '<제79(전)기>' at L19835); ORIG table used L%d"%(TN["line"],TO["line"]))
live=json.load(open(R+"/CSM_waterfall.json",encoding="utf-8"))
hd=json.loads(subprocess.run(["git","-C",R,"show","HEAD:CSM_waterfall.json"],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
lv={r["항목번호"]:r["값"] for r in live if r["원보험사코드"]=="KR0003" and r["공시분기"]=="2023.4Q"}
hv={r["항목번호"]:r["값"] for r in hd if r["원보험사코드"]=="KR0003" and r["공시분기"]=="2023.4Q"}
def items(T):
    v=vec(T); 
    m={1:"기초순보험계약부채",2:"최초인식계약",3:"보험금융손익",4:"보험계약마진을조정하는추정치의변동",5:"보험계약마진상각액",6:"기말순보험계약부채"}
    out={}
    for i,k in m.items():
        x,l=v[k]
        out[i]=(x,l)
    return out
iN=items(TN); iO=items(TO)
bad=[]
Pp("item | printed(백만원) NEW | 억 half-up | exact 억 | live | ok(<=0.051) | HEAD | ORIG printed | ORIG 억 | HEAD==ORIG | line")
for i in range(1,7):
    xn,ln=iN[i]; xo,lo=iO[i]
    sgn=-1 if i==5 else 1
    # item5: printed as (185,905) -> negative; stored negative
    en=eok(xn); ex=eok_exact(xn); eo=eok(xo)
    ok=abs(lv[i]-ex)<=0.0501; okh=abs(hv[i]-eok_exact(xo))<=0.0501
    Pp(i,"|",xn,"|",en,"|",ex,"|",lv[i],"|",ok,"|",hv[i],"|",xo,"|",eo,"|",okh,"| L",ln)
    if not ok: bad.append(("live",i))
    if not okh: bad.append(("calib",i))
cl=iN[1][0]+iN[2][0]+iN[3][0]+iN[4][0]+iN[5][0]-iN[6][0]
Pp("printed rollforward (NEW prior): 기초+신계약+이자+조정+상각-기말 =",cl,"백만원")
clo=iO[1][0]+iO[2][0]+iO[3][0]+iO[4][0]+iO[5][0]-iO[6][0]
Pp("printed rollforward (ORIG current):",clo)
# second witness: audit attachment _00760
tA=load(NEW_AUD); cA=cands(tA)
Pp("AUDIT attachment candidates lines",[t["line"] for t in cA])
for T in cA:
    try:
        iA=items(T); 
        Pp("  audit table L%d:"%T["line"],{i:iA[i][0] for i in range(1,7)}, "== NEW prior vector:", all(abs(iA[i][0]-iN[i][0])<0.5 for i in range(1,7)))
    except KeyError as e: Pp("  audit table L%d: missing %s"%(T["line"],e))
Pp("mismatches:",bad)
# item 3/4 etc: also show sums over product-split? not needed
open(R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte/v11_csm_reread.txt","w",encoding="utf-8").write("\n".join(L))
