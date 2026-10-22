import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
import glob
def show(f,ln,rng=45):
    d=xmlrd.get(R+f)
    ti,t,row,c=xmlrd.row_at_line(d,ln)
    print("FILE",f,"table",t["start"],t["end"])
    start=None
    for rr in t["rows"]:
        lab=rr["cells"][0]["t"] if rr["cells"] else ""
        print(rr["line"],[x["t"][:22] for x in rr["cells"]][:9])
show("data/dart/FY2024_Q1/raw/KR0001_메리츠화재해상보험/20240516001162.xml",48271)
