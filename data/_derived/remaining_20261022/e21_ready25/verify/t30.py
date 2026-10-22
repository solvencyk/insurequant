import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml")
ti,t=d.table_at_line(92782)
print(t["start"],t["end"],d.unit_before(t),len(t["rows"]))
seg=xmlrd.strip(d.text[max(0,t["pos"]-1500):t["pos"]]); print(seg[-300:])
for rr in t["rows"][:14]:
    cs=[c["t"] for c in rr["cells"]]
    print(rr["line"],len(cs),[ (x[:12],c["span"]) for x,c in zip(cs,rr["cells"])][:40])
