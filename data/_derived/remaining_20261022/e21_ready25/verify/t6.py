import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2024_Q2/raw/KR0001_메리츠화재해상보험/20240814003013.xml")
ti,t,row,c=xmlrd.row_at_line(d,51894)
for rr in t["rows"][:8]: print(rr["line"],[(x["t"][:28],x["span"]) for x in rr["cells"]])
print("ROW",row["line"],[(x["t"],x["line"]) for x in row["cells"]])
print(t["start"],t["end"])
