# -*- coding: utf-8 -*-
"""v22: for each gold replacement, read the ORIGINAL filing's prints (both bases) of the relevant line."""
import sys,re,glob,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
def stmts(doc):
    """yield (section_title, table, ) for tables that look like income statement"""
    for t in doc.tables:
        labs=[r["cells"][0]["t"] for r in t["rows"] if r["cells"]]
        if sum(1 for l in labs if re.search(r"보험손익|투자손익|영업이익|당기순이익|분기순이익|반기순이익",l))>=3 and len(t["rows"])>15:
            bt=None
            for pos,ln,txt in reversed([x for x in doc.titles if x[0]<t["pos"]]):
                if "재무제표" in txt and "요약" not in txt: bt=txt;break
            yield bt,t
def find_lines(path,label_re,only=None):
    doc=xmlrd.get(path)
    for bt,t in stmts(doc):
        # header text
        hdr=" | ".join(c["t"] for r in t["rows"][:4] for c in r["cells"] if c["t"])[:120]
        unit=doc.unit_before(t)
        for r in t["rows"]:
            cs=[c["t"] for c in r["cells"]]
            if cs and re.search(label_re,cs[0].replace(" ","")):
                print(f"   [{bt}] T{t['start']} L{r['line']} unit={unit} {cs[0][:30]} -> {cs[1:]}")
CASES=[
 ("KB손보 2023.1Q orig item16 기타사업비용", R+"data/dart/FY2023_Q1/raw/KR0010_KB손해보험/20230515001575.xml", r"기타사업비용"),
 ("KB손보 2023.1Q orig item1 보험손익", R+"data/dart/FY2023_Q1/raw/KR0010_KB손해보험/20230515001575.xml", r"^(Ⅰ\.)?보험손익"),
 ("KB손보 2023.2Q orig item16", R+"data/dart/FY2023_Q2/raw/KR0010_KB손해보험/20230814001763.xml", r"기타사업비용"),
 ("Meritz 2023.1Q orig item16 기타사업비용", R+"data/dart/FY2023_Q1/raw/KR0001_메리츠화재해상보험/20230515002118.xml", r"기타사업비용"),
 ("Meritz 2023.1Q orig 보험손익", R+"data/dart/FY2023_Q1/raw/KR0001_메리츠화재해상보험/20230515002118.xml", r"^보험손익"),
 ("Meritz 2023.2Q orig item16", glob.glob(R+"data/dart/FY2023_Q2/raw/KR0001_메리츠화재해상보험/20230814002723.xml")[0], r"기타사업비용"),
 ("Meritz 2023.2Q orig 보험손익", glob.glob(R+"data/dart/FY2023_Q2/raw/KR0001_메리츠화재해상보험/20230814002723.xml")[0], r"^보험손익"),
]
for nm,p,rx in CASES:
    print("==",nm)
    try: find_lines(p,rx)
    except Exception as e: print("   ERR",e)
