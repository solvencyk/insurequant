import sys,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd,glob
R="C:/Users/sangwook.cho/Desktop/insurequant/"
for f in glob.glob(R+"data/dart/FY2025_Q4/raw/KR0083*/*.xml"):
    print(f)
    d=xmlrd.get(f)
    ti,t=d.table_at_line(35083+20)
    print(t["start"],t["end"])
    for rr in t["rows"][:10]:
        print(rr["line"],[(c["t"][:20],c["span"]) for c in rr["cells"]])
