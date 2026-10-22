# -*- coding: utf-8 -*-
import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
def lines(path,rx,note=""):
    doc=xmlrd.get(path)
    print("==",note,path.split("/")[-1])
    for t in doc.tables:
        labs=[r["cells"][0]["t"] for r in t["rows"] if r["cells"]]
        if sum(1 for l in labs if re.search(r"보험손익|투자손익|영업이익|순이익",l))>=3 and len(t["rows"])>15:
            bt=None
            for pos,ln,txt in reversed([x for x in doc.titles if x[0]<t["pos"]]):
                if "재무제표" in txt and "요약" not in txt: bt=txt;break
            hdr=[c["t"] for r in t["rows"][:3] for c in r["cells"] if c["t"]][:6]
            for r in t["rows"]:
                cs=[c["t"] for c in r["cells"]]
                if cs and re.search(rx,cs[0].replace(" ","")):
                    print(f"   [{bt}] T{t['start']} L{r['line']} unit={doc.unit_before(t)} hdr={hdr} {cs[0][:26]} -> {cs[1:]}")
def f1(pat):
    return glob.glob(R+pat)[0]
lines(f1("data/dart/FY2023_Q1/raw/KR0068_한화생명/xml/20230515002940.xml"), r"^영업이익|Ⅳ\.영업이익|영업외|순이익|^보험손익", "Hanwha 2023.1Q orig")
lines(f1("data/dart/FY2023_Q2/raw/KR0068_한화생명/20230814002953.xml"), r"영업외|^영업이익", "Hanwha 2023.2Q orig")
