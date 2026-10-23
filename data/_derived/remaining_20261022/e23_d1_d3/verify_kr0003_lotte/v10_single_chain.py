# -*- coding: utf-8 -*-
import sys, json, subprocess
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
L=[]
def Pp(*a):
    s=" ".join(str(x) for x in a); L.append(s); print(s)
def head(rel): return json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
live={rel:json.load(open(R+"/"+rel,encoding="utf-8")) for rel in ("PL_breakdown.json","CSM_waterfall.json")}
hd={rel:head(rel) for rel in live}
def grid(rows):
    g={}
    for r in rows:
        if r["원보험사코드"]=="KR0003": g[(r["공시분기"],r["항목번호"])]=(r.get("값"),r.get("값_당분기"))
    return g
PL,PLh=grid(live["PL_breakdown.json"]),grid(hd["PL_breakdown.json"])
CS,CSh=grid(live["CSM_waterfall.json"]),grid(hd["CSM_waterfall.json"])
# (a) 2023.3Q vs FY2024 Q3 own read (prior 9M col idx3, prior 3M col idx2) in raw "원" table
txt=load(R+"/data/dart/FY2024_Q3/raw/KR0003_롯데손해보험/20241114002408.xml")
T=[T for T in tables(txt) if T["line"]==5069][0]
lab2item={"보험손익":1,"투자손익":17,"영업이익(손실)":20,"영업외손익":21,"법인세비용차감전순이익(손실)":22,"법인세비용(주30)":23,"분기순이익(손실)":24,"기타포괄손익(주22)":25,"분기총포괄손익":31}
Pp("(a) 2023.3Q master vs FY2024_Q3 prior columns (own read, table L5069):")
bad=0
for r in T["rows"]:
    if not r: continue
    k=re.sub(r"\s+","",r[0]["t"]); k=re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\.","",k)
    if k in lab2item:
        i=lab2item[k]; v=[num(c["t"]) for c in r[1:] if num(c["t"]) not in (None,"NaN")]
        cum9=v[3]/1e6; m3=v[2]/1e6
        mv=PL[("2023.3Q",i)]
        ok=abs(mv[0]-cum9)<0.0005 and abs(mv[1]-m3)<0.0005
        bad+=0 if ok else 1
        Pp("  item",i,"master 9M",mv[0],"raw 9M",round(cum9,6),"| master 3M",mv[1],"raw 3M",round(m3,6),"->",ok)
Pp("  mismatches:",bad)
# (b) 4Q single recompute
Pp("\n(b) 2023.4Q 값_당분기 vs (4Q cum - 3Q cum):")
issues=[]
for i in range(1,33):
    c4,s4=PL[("2023.4Q",i)]; c3,s3=PL[("2023.3Q",i)]; c4h,s4h=PLh[("2023.4Q",i)]
    moved=(c4h is not None and c4 is not None and abs(c4-c4h)>1e-9)
    der=None if (c4 is None or c3 is None) else c4-c3
    if s4 is None:
        verdict="blank" + (" (cum moved => mixed-vintage seam, blank correct)" if moved and der is not None else (" (3Q cum blank => nothing to derive)" if der is None else " (cum unchanged but single blank?!)"))
        if der is not None and not moved and s4h is not None: issues.append((i,"blanked although cum unchanged"))
    else:
        ok=der is not None and abs(der-s4)<0.001
        verdict="populated, derived %s -> %s%s"%(None if der is None else round(der,6),"OK" if ok else "MISMATCH"," ; cum MOVED but single kept!" if moved else "")
        if not ok or moved: issues.append((i,verdict))
    Pp("  item",i,"cum",c4,"(HEAD",c4h,") single",s4,"(HEAD",s4h,")",verdict)
Pp("  ISSUES:",issues)
# all other quarters' single-quarter fields unchanged vs HEAD (PL + CSM)
chg=[(k,PLh[k],PL[k]) for k in PL if PL[k]!=PLh.get(k) and k[0]!="2023.4Q"]
Pp("  PL cells changed outside 2023.4Q:",chg)
chg=[(k,CSh[k],CS[k]) for k in CS if CS[k]!=CSh.get(k) and k[0]!="2023.4Q"]
Pp("  CSM cells changed outside 2023.4Q:",chg)
# (d) CSM chain
Pp("\n(d) CSM chain (억원)  item: 1 기초,2 신계약,3 이자,4 조정,5 상각,6 기말")
qs=sorted({k[0] for k in CS})
def row(g,q): return [g.get((q,i),(None,None)) for i in range(1,7)]
for tag,g in (("LIVE",CS),("HEAD",CSh)):
    Pp(" --",tag)
    for q in qs:
        r=row(g,q); cum=[x[0] for x in r]; sg=[x[1] for x in r]
        if None in cum: Pp("  ",q,"cum",cum); continue
        close=cum[0]+cum[1]+cum[2]+cum[3]+cum[4]-cum[5]
        sclose=None if None in sg else sg[0]+sg[1]+sg[2]+sg[3]+sg[4]-sg[5]
        Pp("  ",q,"cum",cum,"| cum rollforward gap %.2f"%close,"| single",sg,"| single rollforward gap",None if sclose is None else round(sclose,2))
    # continuity
    Pp("   opening drift within FY / boundary:")
    for fy in (2023,2024):
        op=[g[(f"{fy}.{n}Q",1)][0] for n in (1,2,3,4) if (f"{fy}.{n}Q",1) in g]
        Pp("    FY%d openings Q1..Q4:"%fy,op,"max-min=%.2f"%(max(op)-min(op)),"rel=%.3f%%"%(100*(max(op)-min(op))/min(op)))
    Pp("    FY2023 4Q closing %s -> FY2024 1Q opening %s (diff %.2f)"%(g[("2023.4Q",6)][0],g[("2024.1Q",1)][0],g[("2024.1Q",1)][0]-g[("2023.4Q",6)][0]))
    Pp("    3Q closing -> 4Q single opening:",g[("2023.3Q",6)][0],g[("2023.4Q",1)][1],"; 3Q 9M closing vs 4Q cum opening+flows: Q3 open",g[("2023.3Q",1)][0],"Q4 open",g[("2023.4Q",1)][0])
open(R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte/v10_single_chain.txt","w",encoding="utf-8").write("\n".join(L))
