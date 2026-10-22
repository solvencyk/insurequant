import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2024_Q1/raw/KR0068_한화생명/20240514000837.xml")
for ln in (77509,79268,80843):
    ti,t=d.table_at_line(ln)
    print("== TABLE",t["start"],t["end"],"unit",d.unit_before(t))
    bt=None
    for pos,l,txt in reversed([x for x in d.titles if x[0]<t["pos"]]):
        if "재무제표" in txt and "요약" not in txt: bt=txt;break
    print("section:",bt)
    seg=xmlrd.strip(d.text[max(0,t["pos"]-1500):t["pos"]])
    print("pre:",seg[-300:])
    for rr in t["rows"][:60]:
        cs=[c["t"][:18] for c in rr["cells"]]
        if any("상각" in x for x in cs) or rr is t["rows"][0] or rr["line"]<t["start"]+60:
            print(rr["line"],cs)
