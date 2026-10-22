import sys; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2024_Q2/raw/KR0010_KB손해보험/20240814002750.xml")
ti,t=d.table_at_line(38795)
for rr in t["rows"][:6]: print(rr["line"],[x["t"][:12] for x in rr["cells"]], [x["span"] for x in rr["cells"]])
for rr in t["rows"][-3:]: print(rr["line"],[x["t"][:12] for x in rr["cells"]])
