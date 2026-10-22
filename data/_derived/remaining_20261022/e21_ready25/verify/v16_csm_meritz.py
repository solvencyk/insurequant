# -*- coding: utf-8 -*-
import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
master={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"CSM_waterfall.json",encoding="utf-8"))}
head={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(HERE+"head/CSM_waterfall.json",encoding="utf-8"))}
MK=re.compile(r"전분기|전반기|전3분기|\(전\)|전기|당분기|당반기|당3분기|\(당\)|당기")
CFG={"2023.1Q":("data/dart/FY2024_Q1/raw/KR0001_메리츠화재해상보험/20240516001162.xml",46667),
     "2023.2Q":("data/dart/FY2024_Q2/raw/KR0001_메리츠화재해상보험/20240814003013.xml",50295)}
LAB={1:"기초순장부금액",2:"신계약효과",3:"순보험금융손익",4:"보험계약마진을조정하는추정치",5:"당기손익으로인식한보험계약마진",6:"순장부금액"}
for q,(f,ln) in CFG.items():
    d=xmlrd.get(R+f); ti,t=d.table_at_line(ln)
    hdr=[x["t"] for x in t["rows"][0]["cells"]] if "보험계약마진" in " ".join(x["t"] for x in t["rows"][0]["cells"]) else None
    # header row = first row containing '보험계약마진'
    hrow=None
    for r in t["rows"]:
        if any("보험계약마진" in x["t"] for x in r["cells"]): hrow=r; break
    cols=[i for i,x in enumerate(hrow["cells"]) if "보험계약마진" in x["t"]]
    print("==",q,f.split("/")[-1],"table",t["start"],"unit",d.unit_before(t),"CSM cols",cols,[hrow["cells"][i]["t"] for i in cols])
    # prior marker
    seg=xmlrd.strip(d.text[max(0,t["pos"]-3000):t["pos"]]); ms=list(MK.finditer(seg)); print("  marker:",seg[max(0,ms[-1].start()-6):ms[-1].end()+6] if ms else None)
    bt=[txt for pos,l,txt in reversed([x for x in d.titles if x[0]<t["pos"]]) if "재무제표" in txt][0]
    print("  section:",bt)
    # data rows: take first occurrence after '기초 순장부금액' etc. The table may contain 3개월/누적 pairs
    rows=[]
    for r in t["rows"]:
        cs=[x["t"] for x in r["cells"]]
        rows.append((r["line"],cs))
    def val(label_key, which=0, endswith=False):
        hits=[(ln_,cs) for ln_,cs in rows if cs and (cs[0].replace(" ","").endswith(label_key) if endswith else cs[0].replace(" ","").startswith(label_key))]
        return hits
    for it in (1,2,3,4,5,6):
        key=LAB[it]
        hits=val(key, endswith=(it==6))
        if it==6: hits=[h for h in hits if "분기말" in h[1][0] or "반기말" in h[1][0]]
        if not hits: print("  item",it,"no row"); continue
        ln_,cs=hits[0]
        # if table has 3개월/누적 pairs the CSM columns repeat; detect by len
        nvals=len(cs)-1
        print("   item",it,cs[0][:20],"L",ln_,"ncells",len(cs), end=" ")
        # sum CSM columns (index offsets by header)
        tot=0
        for ci in cols:
            v=xmlrd.parse_num(cs[ci]) if ci<len(cs) else None
            tot+=0 if v is None else v
        eok=tot/100.0
        m=master[("KR0001",q,it)]; h=head[("KR0001",q,it)]
        print("sum CSM cols =",tot,"mn ->",round(eok,3),"eok  master",m,"head",h,"" if abs(eok-m)<=0.051 else "  <== DIFF")
