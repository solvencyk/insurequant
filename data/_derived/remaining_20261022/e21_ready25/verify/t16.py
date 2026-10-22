import sys,re; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2025_Q2/raw/KR0003_롯데손해보험/xml/20250814003966.xml")
for ln in (58037,59020,59560,60274,61879):
    ti,t=d.table_at_line(ln)
    print("== TABLE",t["start"])
    for rr in t["rows"]: print(rr["line"],[(x["t"][:22]) for x in rr["cells"]], "|", [x["span"] for x in rr["cells"]][:12])
