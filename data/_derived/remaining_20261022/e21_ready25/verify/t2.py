import sys,re; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2024_Q1/raw/KR0001_메리츠화재해상보험/20240516001162.xml")
ti,t,row,c=xmlrd.row_at_line(d,48271)
print(t["start"],t["end"],len(t["rows"]))
for rr in t["rows"][:14]: print(rr["line"],[x["t"][:30] for x in rr["cells"]])
# paragraphs before table
seg=d.text[max(0,t["pos"]-2500):t["pos"]]
print(xmlrd.strip(seg)[-700:])
