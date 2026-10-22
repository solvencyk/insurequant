import json,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
def load(p,key="값"):
    d={}
    for r in json.load(open(p,encoding="utf-8")): d[(r["원보험사코드"],r["공시분기"],r["항목번호"])]=r.get(key)
    return d
n=load(R+"PL_breakdown.json"); o=load(HERE+"head/PL_breakdown.json")
cn=load(R+"CSM_waterfall.json"); co=load(HERE+"head/CSM_waterfall.json")
NM={"KR0104":"농협생명","KR0083":"푸본현대","KR0070":"ABL","KR0079":"미래에셋","KR0010":"KB손보","KR0099":"KB라이프","KR0003":"롯데손보","KR0001":"메리츠","KR0068":"한화생명"}
cells=json.load(open(HERE+"v01_PL_breakdown_cells.json",encoding="utf-8"))
cq=sorted({(k[0],k[1]) for k,f,a,b in cells if f=="값"})
cqc=sorted({(k[0],k[1]) for k,f,a,b in json.load(open(HERE+"v01_CSM_waterfall_cells.json",encoding="utf-8")) if f=="값"})
def f(x): return "blank" if x is None else f"{x/100:,.1f}"
lines=["company quarter | 보험손익 | 투자손익 | 당기순이익 | OCI | 총포괄 (억원, 전 -> 후)"]
for c,q in cq:
    row=[]
    for it in (1,17,24,25,31):
        a,b=o.get((c,q,it)),n.get((c,q,it))
        row.append("same" if a==b else f"{f(a)}->{f(b)}")
    lines.append(f"{NM[c]} {q} | "+" | ".join(row))
lines.append("")
lines.append("CSM (억원): company quarter | 기초 | 신계약 | 이자 | 가정 | 상각 | 기말")
for c,q in cqc:
    row=[]
    for it in range(1,7):
        a,b=co.get((c,q,it)),cn.get((c,q,it))
        row.append("same" if a==b else f"{a}->{b}")
    pct=None
    a,b=co.get((c,q,6)),cn.get((c,q,6))
    lines.append(f"{NM[c]} {q} | "+" | ".join(row)+("" if a in (None,0) or a==b else f"  [기말 {((b-a)/a*100):+.2f}%]"))
open(HERE+"v42_headline_table.txt","w",encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
