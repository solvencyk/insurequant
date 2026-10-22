import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
f=glob.glob(R+"data/dart/FY2024_Q3/raw/KR0003*/20241114002408.xml")[0]
d=xmlrd.get(f)
for t in d.tables:
    for r in t["rows"]:
        cs=[c["t"] for c in r["cells"]]
        if cs and cs[0].replace(" ","")=="보험계약마진상각" and any(x in ("131,623","171,871","57,139","50,... ") for x in cs):
            seg=xmlrd.strip(d.text[max(0,t["pos"]-700):t["pos"]])
            print(t["start"],r["line"],cs,"| pre:",seg[-60:])
