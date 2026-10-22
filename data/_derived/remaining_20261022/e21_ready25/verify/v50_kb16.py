import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
for fy,q,label in ((2025,4,"FY2025_Q4 (prior=2024.4Q)"),(2025,3,"FY2025_Q3 (prior=2024.3Q)")):
    fs=[x for x in glob.glob(R+f"data/dart/FY{fy}_Q{q}/raw/KR0010*/*.xml")+glob.glob(R+f"data/dart/FY{fy}_Q{q}/raw/KR0010*/xml/*.xml") if not x.endswith("_00760.xml")]
    d=xmlrd.get(fs[0]); print("==",label,fs[0].split("/")[-1])
    for t in d.tables:
        labs=[re.sub(r"\s+","",r["cells"][0]["t"]) for r in t["rows"] if r["cells"]]
        if sum(1 for l in labs if re.search(r"보험손익|투자손익|영업이익|순이익",l))>=3 and len(t["rows"])>15:
            bt=None
            for pos,ln,txt in reversed([x for x in d.titles if x[0]<t["pos"]]):
                if "재무제표" in txt and "요약" not in txt: bt=txt;break
            if bt and "연결" not in bt and "주석" not in bt:
                for r in t["rows"]:
                    cs=[c["t"] for c in r["cells"]]
                    if cs and re.search(r"기타사업비용",re.sub(r"\s+","",cs[0])): print("  ",bt,"L",r["line"],cs[0],[x for x in cs[1:] if x])
