import sys; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2025_Q3/raw/KR0003_롯데손해보험/xml/20251114002985.xml")
for ln in (32050,32844,33198,33520):
    ti,t=d.table_at_line(ln)
    print("== TABLE",t["start"])
    for rr in t["rows"][6:]: print(rr["line"],[(x["t"][:26]) for x in rr["cells"]])
