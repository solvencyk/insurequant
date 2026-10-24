# -*- coding: utf-8 -*-
import sys, json, re
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent")
from w02_lib import *
sys.stdout.reconfigure(encoding="utf-8")
PLr=json.load(open(R+"PL_breakdown.json",encoding="utf-8"))
PL={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r for r in PLr}
chg=json.load(open(R+"data/_derived/remaining_20261022/e25_followups/pass4/verify_independent/w01_changes.json",encoding="utf-8"))
CH={(tuple(k)[0],tuple(k)[1],tuple(k)[2],f) for k,f,a,b in chg}
FQ={"2023.1Q":"FY2024_Q1","2023.2Q":"FY2024_Q2","2023.3Q":"FY2024_Q3"}
out=[]; bad=0; tot=0
def W(s): print(s); out.append(s)
def stmt(fq):
    p=raw_path(fq,"KR0032")
    ts=[t for t in read_tables(p) if any(r["cells"] and r["cells"][0].replace(" ","").startswith("VI.법인세차감전순이익") for r in t["rows"])]
    assert len(ts)==1,(fq,len(ts))
    t=ts[0]; rows={}
    for r in t["rows"]:
        if not r["cells"]: continue
        lab=r["cells"][0].replace(" ","")
        nums=[to_num(c) for c in r["cells"][1:5]]
        if len(r["cells"])>=5 and all(n is not None for n in nums):
            rows.setdefault(lab,[]).append((r["line"],[n/1e6 for n in nums]))
    return p,t["line"],rows
def one(rows,lab):
    v=rows.get(lab.replace(" ",""))
    assert v and len(v)==1,(lab,v)
    return v[0]
for q,fq in FQ.items():
    p,tl,rows=stmt(fq)
    W("## %s %s table@%d"%(q,p.split("raw")[-1],tl))
    # numbers order: cur3m, curcum, prior3m, priorcum
    def val(lab,col): return one(rows,lab)[1][col]
    def ln(lab): return one(rows,lab)[0]
    def calc(col):
        d={}
        d[1]=val("I.보험손익",col); d[16]=val("3)기타사업비용",col); d[17]=val("II.투자손익",col)
        fin=val("1)보험금융수익",col)+val("2)재보험금융수익",col)-val("1)보험금융비용",col)-val("2)재보험금융비용",col)
        d[19]=fin
        d[18]=(val("1.투자영업수익",col)-val("1)보험금융수익",col)-val("2)재보험금융수익",col))-(val("2.투자영업비용",col)-val("1)보험금융비용",col)-val("2)재보험금융비용",col))
        d[20]=val("III.영업이익",col); d[21]=val("IV.영업외수익",col)-val("V.영업외비용",col)
        d[22]=val("VI.법인세차감전순이익",col); d[23]=val("VII.법인세비용",col); d[24]=val("VIII."+("반기순이익" if q=="2023.2Q" else "분기순이익" if True else ""),col) if False else None
        # net income label differs by filing
        for lab in ("VIII.반기순이익","VIII.분기순이익","VIII.당기순이익"):
            if lab in rows: d[24]=val(lab,col)
        d[25]=val("IX.기타포괄손익",col); d[26]=val("기타포괄손익-공정가치측정금융자산관련손익",col) if "기타포괄손익-공정가치측정금융자산관련손익" in rows else None
        d[27]=val("보험금융순손익",col); d[28]=val("현금흐름위험회피파생상품평가손익",col) if "현금흐름위험회피파생상품평가손익" in rows else None
        d[29]=val("기타포괄손익-공정가치측정유가증권평가손익",col) if "기타포괄손익-공정가치측정유가증권평가손익" in rows else None
        d[30]=val("재보험금융순손익",col); d[31]=val("X.총포괄손익",col); d[32]=val("확정급여제도의재측정요소",col) if "확정급여제도의재측정요소" in rows else None
        return d
    cum=calc(3); sgl=calc(2)
    # item15: no row
    W("  item15 label '기타영업수익' present in table: %s"%any("기타영업수익" in k for k in rows))
    for it in sorted(cum):
        for fld,src in (("값",cum),("값_당분기",sgl)):
            raw=src[it]
            if fld=="값_당분기" and q=="2023.1Q": raw=cum[it]
            m=PL.get(("KR0032",q,it),{}).get(fld)
            tot+=1
            if raw is None:
                W("  n/a   item%2d %-9s master=%s (label missing in this filing)"%(it,fld,m)); continue
            ok = m is not None and abs(raw-m)<=2e-6
            flag="CHG" if ("KR0032",q,it,fld) in CH else "   "
            if not ok: bad+=1
            W("  %s %s item%2d %-9s raw=%.6f master=%s"%("OK " if ok else "BAD",flag,it,fld,raw,m))
    # identities on MASTER values
for q in FQ:
    g=lambda it,f="값": (PL.get(("KR0032",q,it),{}).get(f))
    for f in ("값","값_당분기"):
        def chk(name,a,b):
            global bad,tot
            tot+=1
            if a is None or b is None: W("IDN SKIP(missing) %s %s %s"%(q,f,name)); return
            ok=abs(a-b)<=2e-5
            if not ok: bad+=1
            W("IDN %s %s %s %-14s lhs=%.6f rhs=%.6f diff=%.6f"%("OK " if ok else "BAD",q,f,name,a,b,a-b))
        if g(1,f) is None and g(17,f) is None: continue
        chk("1+17=20",(g(1,f) or 0)+(g(17,f) or 0),g(20,f))
        chk("17=18+19",g(17,f),(g(18,f) or 0)+(g(19,f) or 0) if g(18,f) is not None and g(19,f) is not None else None)
        chk("20+21=22",(g(20,f) or 0)+(g(21,f) or 0),g(22,f))
        if g(22,f) is not None and g(23,f) is not None and g(24,f) is not None: chk("22-23=24",g(22,f)-g(23,f),g(24,f))
        if g(24,f) is not None and g(25,f) is not None: chk("24+25=31",g(24,f)+g(25,f),g(31,f))
    # bridge 1 = 2+13+14+15-16
    a=[g(i) or 0 for i in (2,13,14,15)]
    W("BRIDGE %s cum: 2+13+14+15-16 = %.6f vs item1 %.6f resid %.3f"%(q,sum(a)-(g(16) or 0),g(1),g(1)-(sum(a)-(g(16) or 0))))
W("TOTAL checks %d BAD %d"%(tot,bad))
open(R+"data/_derived/remaining_20261022/e25_followups/pass4/verify_independent/w05_nh_verify.txt","w",encoding="utf-8").write("\n".join(out)+"\n")
