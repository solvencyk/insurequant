# -*- coding: utf-8 -*-
import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
master={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"CSM_waterfall.json",encoding="utf-8"))}
head={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(HERE+"head/CSM_waterfall.json",encoding="utf-8"))}
MK=re.compile(r"전분기|전반기|전3분기|\(전\)|전기|당분기|당반기|당3분기|\(당\)|당기")
def trailing(cs,n):
    vals=[]
    for x in cs:
        v=xmlrd.parse_num(x)
        if v is None and x.strip() in ("-","0"): v=0.0
        vals.append(v)
    t=vals[-n:]
    return t if len(t)==n and all(v is not None for v in t) else None
# ---- wide (2024.2Q, 2024.3Q)
for q,f,ln in (("2024.2Q","data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml",92782),("2024.3Q","data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml",50033)):
    d=xmlrd.get(R+f); ti,t=d.table_at_line(ln)
    seg=xmlrd.strip(d.text[max(0,t["pos"]-600):t["pos"]]); 
    print("==",q,"table",t["start"],t["end"],"unit",d.unit_before(t),"| pre:",seg[-45:])
    print("   section:",[txt for pos,l,txt in reversed([x for x in d.titles if x[0]<t["pos"]]) if "재무제표" in txt][0])
    hdr=[xmlrd.strip(c["t"]) for r in t["rows"][:8] for c in r["cells"] if c["t"] and ("사망" in c["t"] or "건강" in c["t"] or "연금" in c["t"] or "저축" in c["t"] or "기타보험" in c["t"])]
    print("   product headers:",hdr)
    out={}
    for r in t["rows"]:
        cs=[c["t"] for c in r["cells"]]
        tl=trailing(cs,25)
        if tl is None: continue
        csm=sum(tl[5*g+i] for g in range(5) for i in (2,3,4))
        lab=" / ".join(x for x in cs[:2] if x)[:48]
        out[r["line"]]=(lab,csm)
        print("   L%d %-50s CSMsum=%s mn(원)->%.2f eok"%(r["line"],lab,f"{csm:,.0f}",csm/1e8))
