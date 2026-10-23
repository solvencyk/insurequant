# -*- coding: utf-8 -*-
"""Independent re-read of KR0003 FY2023 (2023.4Q) cumulative PL + CSM from raw XML. Stdlib + own vlib only."""
import sys, json
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
L=[]
def P(*a):
    s=" ".join(str(x) for x in a); L.append(s); print(s)
def clean(s): return re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\.","",re.sub(r"\s+","",s))
def stmt(txt, col):
    """income statement 4-2 table: label -> (value in 백만원, line) using column index col (0=current,1=prior)"""
    s4=txt.count("\n",0,txt.find("4-2. 포괄손익계산서"))+1; e4=txt.count("\n",0,txt.find("4-3. 자본변동표"))+1
    Ts=[T for T in tables(txt) if s4<T["line"]<e4 and T["rows"] and any(r and "보험손익" in r[0]["t"] and r[0]["t"].startswith("Ⅰ") for r in T["rows"])]
    T=[t for t in Ts if txt[:0]=="" ][0]
    hdr=" ".join(c["t"] for r in T["rows"][:3] for c in r)
    out={}
    for r in T["rows"]:
        if len(r)<2: continue
        v=[c for c in r[1:] if num(c["t"]) not in (None,"NaN")]
        if col<len(v): out.setdefault(clean(r[0]["t"]),(num(v[col]["t"])/1e6,v[col]["line"]))
    return out,hdr,T["line"]
def lob(txt,k):
    """k-th table containing the life/general/auto 보험손익 note (보험수익 .. 총 재보험비용)"""
    Ts=[T for T in tables(txt) if T["rows"] and any(r and r[0]["t"].strip()=="총 재보험비용" for r in T["rows"]) and any(r and r[0]["t"].strip()=="보험계약마진 상각" for r in T["rows"]) and any(r and r[0]["t"].strip()=="일반모형 적용 보험수익" for r in T["rows"])]
    T=Ts[k]; rows={}; sec=None
    for r in T["rows"]:
        if not r: continue
        lab=r[0]["t"].strip()
        nums=[num(c["t"]) for c in r[1:]]
        key=re.sub(r"\s+","",lab)
        n=1
        while key in rows: n+=1; key=re.sub(r"\s+","",lab)+"#%d"%n
        rows[key]=(nums,r[0]["line"])
    return rows,T,[T2["line"] for T2 in Ts]
def pl_items(txt, col):
    s,hdr,tl=stmt(txt,col)
    g=lambda k:s[clean(k)]
    d={}
    d[1]=g("보험손익"); d[17]=g("투자손익"); d[16]=g("(3)기타사업비용(주35)")
    d[20]=g("영업이익(손실)"); d[21]=g("영업외손익"); d[22]=g("법인세비용차감전순이익(손실)"); d[23]=g("법인세비용(주37)"); d[24]=g("당기순이익(손실)")
    d[25]=g("기타포괄손익(주28)"); d[26]=g("(1)기타포괄손익-공정가치측정채무증권평가손익"); d[27]=g("(4)보험계약자산(부채)순금융손익"); d[28]=g("(3)위험회피목적파생상품평가손익"); d[29]=g("(1)기타포괄손익-공정가치측정지분증권평가손익"); d[30]=g("(5)재보험계약자산(부채)순금융손익"); d[31]=g("총포괄손익")
    # 19 = (보험금융수익 + 재보험금융수익) - (보험금융비용 + 재보험금융비용)
    keys=list(s)
    a=s[clean("(1)보험금융수익(주33)")]; b=s[clean("(2)재보험금융수익(주33)")]; c=s[clean("(1)보험금융비용(주33)")]; e=s[clean("(2)재보험금융비용(주33)")]
    d[19]=(a[0]+b[0]-c[0]-e[0],"%d+%d-%d-%d"%(a[1],b[1],c[1],e[1]))
    d[18]=(d[17][0]-d[19][0],"17-19")
    d[32]=(None,"")  # computed below
    try:
        d[32]=(g("2.당기손익으로재분류되지않는세후기타포괄손익의구성요소")[0]-d[29][0]+g("(2)기타포괄손익-공정가치측정채무증권신용손실")[0],"(2.비재분류 - 29 + 신용손실)")
    except KeyError: pass
    return d,hdr,tl
def lob_items(rows):
    gg=lambda k,i=0:rows[re.sub(r"\s+","",k)][0][i]
    ln=lambda k:rows[re.sub(r"\s+","",k)][1]
    d={}
    ins_rev=gg("총 보험수익"); ins_cost=gg("총 보험비용"); re_rev=gg("총 재보험수익"); re_cost=gg("총 재보험비용")
    d[3]=(ins_rev-ins_cost,"총 보험수익(장기)-총 보험비용(장기) L%d,L%d"%(ln("총 보험수익"),ln("총 보험비용")))
    d[4]=(gg("보험계약마진 상각"),"L%d"%ln("보험계약마진 상각"))
    d[5]=(gg("위험조정 변동"),"L%d"%ln("위험조정 변동"))
    d[6]=(gg("예상보험금 및 예상기타보험서비스비용")-gg("발생보험금 및 기타서비스비용"),"예상 L%d - 발생 L%d"%(ln("예상보험금 및 예상기타보험서비스비용"),ln("발생보험금 및 기타서비스비용")))
    d[8]=(re_rev-re_cost,"총 재보험수익-총 재보험비용 L%d,L%d"%(ln("총 재보험수익"),ln("총 재보험비용")))
    d[9]=(-gg("보험계약마진 상각#2"),"-L%d"%ln("보험계약마진 상각#2"))
    d[10]=(-gg("위험조정 변동#2") if False else gg("위험조정 변동#2"),"L%d (sign as printed in 재보험비용 section: -> master sign check)"%ln("위험조정 변동#2"))
    d[11]=(gg("발생보험금 및 기타재보험수익")-gg("회수예상 보험금 및 기타보험서비스비용"),"발생 L%d - 회수예상 L%d"%(ln("발생보험금 및 기타재보험수익"),ln("회수예상 보험금 및 기타보험서비스비용")))
    d[2]=(d[3][0]+d[8][0],"3+8")
    d[7]=(d[3][0]-(d[4][0]+d[5][0]+d[6][0]),"3-(4+5+6) using item6 from this vintage")
    d[12]=(d[8][0]-(d[9][0]+d[10][0]+d[11][0]),"8-(9+10+11)")
    ac=lambda i:(gg("총 보험수익",3 if False else i),)
    return d
txtN=load(NEW); txtO=load(ORIG)
res={}
# ---------- NEW filing prior column
dN,hdrN,tlN=pl_items(txtN,1)
P("NEW stmt table line",tlN,"header:",hdrN[:200])
rowsN,TN,linesN=lob(txtN,1)
P("NEW LOB candidate tables (lines):",linesN,"using k=1 at line",TN["line"],"pre:",TN["pre"][-60:])
lobN=lob_items(rowsN)
# ---------- ORIG filing current column (calibration)
dO,hdrO,tlO=pl_items(txtO,0)
P("ORIG stmt table line",tlO,"header:",hdrO[:200])
rowsO,TO,linesO=lob(txtO,0)
P("ORIG LOB candidate tables (lines):",linesO,"using k=0 at line",TO["line"],"pre:",TO["pre"][-60:])
lobO=lob_items(rowsO)
# ---------- compare with master
R_="C:/Users/sangwook.cho/Desktop/insurequant"
import subprocess
live=json.load(open(R_+"/PL_breakdown.json",encoding="utf-8"))
headb=json.loads(subprocess.run(["git","-C",R_,"show","HEAD:PL_breakdown.json"],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
lv={r["항목번호"]:r["값"] for r in live if r["원보험사코드"]=="KR0003" and r["공시분기"]=="2023.4Q"}
hv={r["항목번호"]:r["값"] for r in headb if r["원보험사코드"]=="KR0003" and r["공시분기"]=="2023.4Q"}
P("\nitem | live | NEW-prior expected | ok(tol 0.5) | HEAD | ORIG-current expected | HEAD==ORIG(tol .5) | line(s)")
bad=[]
for i in range(1,33):
    n=dN.get(i) or lobN.get(i); o=dO.get(i) or lobO.get(i)
    nv=n[0] if n else None; ov=o[0] if o else None
    ok=None if nv is None or lv.get(i) is None else abs(lv[i]-nv)<=0.5
    okh=None if ov is None or hv.get(i) is None else abs(hv[i]-ov)<=0.5
    P(i,"|",lv.get(i),"|",None if nv is None else round(nv,6),"|",ok,"|",hv.get(i),"|",None if ov is None else round(ov,6),"|",okh,"|",n[1] if n else "")
    if ok is False: bad.append(("live!=NEW",i,lv.get(i),nv))
    if okh is False: bad.append(("HEAD!=ORIG(calibration)",i,hv.get(i),ov))
P("\nMISMATCHES:",bad)
open(R_+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte/v08_reread_pl.txt","w",encoding="utf-8").write("\n".join(L))
