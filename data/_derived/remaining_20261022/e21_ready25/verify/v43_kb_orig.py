import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
def show(path,label_rx,note):
    d=xmlrd.get(path); print("==",note,path.split("/")[-1])
    for t in d.tables:
        labs=[re.sub(r"\s+","",r["cells"][0]["t"]) for r in t["rows"] if r["cells"]]
        if sum(1 for l in labs if re.search(r"보험손익|투자손익|영업이익|순이익",l))>=3 and len(t["rows"])>15:
            bt=None
            for pos,ln,txt in reversed([x for x in d.titles if x[0]<t["pos"]]):
                if "재무제표" in txt and "요약" not in txt: bt=txt;break
            if not bt or "주석" in bt: continue
            hdr=[c["t"] for r in t["rows"][:4] for c in r["cells"] if c["t"]][:8]
            for r in t["rows"]:
                cs=[c["t"] for c in r["cells"]]
                if cs and re.search(label_rx,re.sub(r"\s+","",cs[0])):
                    print(f"   [{bt}] hdr={hdr} L{r['line']} {cs[0][:20]} -> {[x for x in cs[1:] if x]}")
show(R+"data/dart/FY2023_Q1/raw/KR0010_KB손해보험/20230515001575.xml",r"^(Ⅰ\.)?보험손익|^(Ⅱ\.)?투자손익|^(Ⅲ\.)?영업이익|^(Ⅶ\.)?(분기)?순이익","KB orig 2023.1Q")
show(R+"data/dart/FY2024_Q1/raw/KR0010_KB손해보험/20240516001008.xml",r"^(Ⅰ\.)?보험손익|^(Ⅱ\.)?투자손익|^(Ⅲ\.)?영업이익|^(Ⅶ\.)?(분기)?순이익","KB next-year FY2024_Q1")
