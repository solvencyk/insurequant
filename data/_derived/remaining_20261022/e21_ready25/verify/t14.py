import sys; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2024_Q1/raw/KR0003_롯데손해보험/20240516001888.xml")
ti,t=d.table_at_line(20526)
print(t["start"],t["end"])
for rr in t["rows"]: print(rr["line"],[x["t"][:20] for x in rr["cells"]],[x["span"] for x in rr["cells"]] if rr["line"]<20560 else "")
d=xmlrd.get(R+"data/dart/FY2024_Q2/raw/KR0003_롯데손해보험/20240814002875.xml")
ti,t=d.table_at_line(22710)
print(t["start"],t["end"])
for rr in t["rows"][:12]: print(rr["line"],[x["t"][:20] for x in rr["cells"]],[x["span"] for x in rr["cells"]])
