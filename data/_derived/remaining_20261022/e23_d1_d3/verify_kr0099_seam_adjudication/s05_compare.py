# -*- coding: utf-8 -*-
"""KR0099 KB Life: do 2023.1Q-3Q (new, FY2024 interim prior cols) and 2023.4Q (FY2023 annual current) form ONE vintage?
Own stdlib reader (vlib); filings read directly; master via git show HEAD and the live file (read-only)."""
import sys, json, subprocess
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_seam_adjudication/"
lines=[]
def P(*a):
    s=" ".join(str(x) for x in a); lines.append(s); print(s)
def head(rel):
    return json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
def cm(rows):
    return {(r["항목번호"],r["공시분기"]):(r["값"],r["값_당분기"]) for r in rows if r["원보험사코드"]=="KR0099"}
PLH=cm(head("PL_breakdown.json")); PLL=cm(json.load(open(R+"/PL_breakdown.json",encoding="utf-8")))
def is_table(q):
    tb=tables(load(XML[q]))
    c=[t for t in tb if "4-2. 포괄손익계산서" in t["pre"][-260:] and len(t["rows"])>30]
    assert len(c)==1,(q,len(c))
    d={}
    for r in c[0]["rows"]:
        cells=[x for x,_ in r]
        if len(cells)<3: continue
        lab=cells[0]; occ=sum(1 for k in d if k[0]==lab)
        d[(lab,occ)]=[num(x) if x!="" else None for x in cells[1:]]
    return d
def z(v): return 0.0 if v is None else v
def col(d,lab,i,occ=0):
    a=d.get((lab,occ)); 
    return None if a is None else a[i]
NI=["분기순이익","당기순이익(손실)","당기순이익"]
def ni(d,i):
    for l in NI:
        if (l,0) in d: return col(d,l,i)
def items(d,i,style):
    """style 'orig' (2023 filings: 투자영업손익 gross of 보험금융) or 'new2024' (2024 interim: 투자영업손익 already net)"""
    r={}
    r[1]=col(d,"보험영업손익",i); r[20]=col(d,"영업이익",i); r[22]=col(d,"법인세비용차감전순이익",i); r[23]=col(d,"법인세비용",i)
    r[24]=ni(d,i); r[25]=col(d,"기타포괄손익",i); r[27]=col(d,"보험계약자산부채순금융손익",i); r[31]=col(d,"총포괄손익",i)
    r[3]=col(d,"보험영업수익",i,1)-col(d,"보험영업비용",i,1)
    r[8]=z(col(d,"재보험영업수익",i))-z(col(d,"재보험영업비용",i))
    r[2]=r[3]+r[8]
    if style=="orig":
        r[19]=col(d,"보험금융손익",i); r[17]=col(d,"투자영업손익",i)+r[19]
    else:
        fin=z(col(d,"보험금융수익",i))+z(col(d,"재보험금융수익",i)); finc=z(col(d,"보험금융비용",i))+z(col(d,"재보험금융비용",i))
        r[19]=fin-finc; r[17]=col(d,"투자영업손익",i)
    return r
d233=is_table("2023.3Q"); d234=is_table("2023.4Q"); d243=is_table("2024.3Q"); d244=is_table("2024.4Q")
a_orig9=items(d233,1,"orig")      # (c) FY2023 Q3 filing, current 9M cum (original, policy A)
a_new9 =items(d243,3,"new2024")   # (a) FY2024 Q3 filing, prior-year 9M cum
b_ann  =items(d234,0,"orig")      # (b) FY2023 annual, current column
d_ann24=items(d244,1,"new2024")   # (d) FY2024 annual, prior-year column (further restated, owner D1 option B excludes)
P("== units: 백만원. columns: c=FY2023 Q3 original 9M | a=FY2024 Q3 prior-year 9M | b=FY2023 annual current (= master 2023.4Q cum) | d=FY2024 annual prior col (2nd restatement)")
P("== master columns: HEADq3 (old 3Q cum) / LIVEq3 (new 3Q cum) / q4 (HEAD=LIVE)")
P(f"{'item':>4} {'c(orig9M)':>11} {'a(24Q3pri)':>11} {'b(annual)':>11} {'d(24ann pri)':>12} | {'HEADq3':>10} {'LIVEq3':>10} {'q4':>10} | chk c=HEADq3 a=LIVEq3 b=q4 | a-c    d-b")
res={}
for it in (1,2,3,17,19,20,22,23,24,25,27,31):
    c,a,b,d=a_orig9[it],a_new9[it],b_ann[it],d_ann24[it]
    hq,lq,q4=PLH[(it,"2023.3Q")][0],PLL[(it,"2023.3Q")][0],PLL[(it,"2023.4Q")][0]
    hq4=PLH[(it,"2023.4Q")][0]
    ok=lambda x,y: "ok" if y is not None and abs(x-y)<=1.0 else "DIFF"
    P(f"{it:>4} {c:>11.0f} {a:>11.0f} {b:>11.0f} {d:>12.0f} | {hq:>10.0f} {lq:>10.0f} {q4:>10.0f} | {ok(c,hq)} {ok(a,lq)} {ok(b,q4)} (q4 head==live {hq4==q4}) | {a-c:>7.0f} {d-b:>7.0f}")
    res[it]=(c,a,b,d,hq,lq,q4)
for it in (4,7):
    hq,lq,q4=PLH[(it,"2023.3Q")][0],PLL[(it,"2023.3Q")][0],PLL[(it,"2023.4Q")][0]
    P(f"{it:>4} (note-derived; master only) HEADq3={hq} LIVEq3={lq} q4={q4}")
    res[it]=(None,None,None,None,hq,lq,q4)
P("\n== DART-printed restatement bridge in the FY2023 annual report itself (note 'accounting-policy change, retrospective', separate statements, 2023-09-30 summary P&L, 백만원)")
P("   before(A) -> after(B): 보험영업손익 207,078->215,121 | 보험금융손익 -764,100->-773,564 | 영업이익 396,956->395,535 | 세전 396,252->394,831 | 법인세 99,378->98,969 | 순이익 296,874->295,862")
P("   B column == FY2024 Q3 prior-year 9M column (a) within 1 (rounding):", all(abs(x-y)<=1 for x,y in [(215121,a_new9[1]),(-773564,a_new9[19]),(395535,a_new9[20]),(394831,a_new9[22]),(98969,a_new9[23]),(295862,a_new9[24])]))
P("   A column == FY2023 Q3 original 9M column (c):", all(abs(x-y)<=1 for x,y in [(207078,a_orig9[1]),(-764100,a_orig9[19]),(396956,a_orig9[20]),(396252,a_orig9[22]),(99378,a_orig9[23]),(296874,a_orig9[24])]))
P("\n== 4Q single quarter = annual(b) - 9M, in 억원 (백만원/100)")
P(f"{'item':>4} {'READ-NEW (loaded: b-a)':>24} {'READ-OLD (HEAD: b-c)':>22} {'gap(new-old)':>13} | {'ticket claim: d-a':>18}")
tot=0; n=0
for it in (1,2,3,17,19,20,22,23,24,25,27,31,4,7):
    c,a,b,d,hq,lq,q4=res[it]
    new=(q4-lq)/100; old=(q4-hq)/100
    tk=((d-a)/100) if d is not None else None
    P(f"{it:>4} {new:>24.1f} {old:>22.1f} {new-old:>13.1f} | {('%.1f'%tk) if tk is not None else '   n/a':>18}")
P("\nstored 값_당분기 2023.4Q LIVE (백만원):",{it:PLL[(it,"2023.4Q")][1] for it in (1,2,3,4,7,17,19,20,22,23,24,25,27,31)})
open(OUT+"s05_compare.txt","w",encoding="utf-8").write("\n".join(lines))
