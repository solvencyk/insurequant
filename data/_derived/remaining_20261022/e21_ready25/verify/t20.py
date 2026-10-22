import sys,json,csv; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
rows=list(csv.DictReader(open(R+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv",encoding="utf-8-sig")))
for r in rows:
    if r["sheet"]=="PL" and r["code"]=="KR0068" and r["quarter"]=="2023.1Q" and r["item"] in ("2","3","8","4","7","12"):
        print(r["item"],r["old"],r["new"],r["cite(label|line|text)"],"|",r["how"])
d=xmlrd.get(R+"data/dart/FY2024_Q1/raw/KR0068_한화생명/20240514000837.xml")
ti,t=d.table_at_line(66068) if False else d.table_at_line(66200)
print(t["start"],t["end"])
for rr in t["rows"][:40]:
    cs=[c["t"] for c in rr["cells"]]
    print(rr["line"],cs[0][:40],"|",cs[-1])
