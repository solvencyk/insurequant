import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2025_Q1/raw/KR0079_미래에셋생명/20250515001717.xml")
ti,t=d.table_at_line(42937)
print(t["start"],t["end"],d.unit_before(t))
seg=xmlrd.strip(d.text[max(0,t["pos"]-1500):t["pos"]]); print(seg[-300:])
for rr in t["rows"]:
    cs=[c["t"] for c in rr["cells"]]
    print(rr["line"],[x[:14] for x in cs], [c["span"] for c in rr["cells"]][:3])
