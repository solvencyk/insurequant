import sys,re; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2024_Q1/raw/KR0001_메리츠화재해상보험/20240516001162.xml")
ti,t=d.table_at_line(46667)
print(t["start"],t["end"],d.unit_before(t))
seg=xmlrd.strip(d.text[max(0,t["pos"]-2500):t["pos"]])
print(seg[-400:])
for rr in t["rows"]:
    cs=[c["t"] for c in rr["cells"]]
    print(rr["line"],[x[:16] for x in cs])
